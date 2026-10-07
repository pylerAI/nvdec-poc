"""Per-stage timers for vLLM 0.28.0 serving Nemotron 3 Nano Omni (live 6 s 360p MPEG-TS stage breakdown).

Active only when STAGE_TIMING_DIR is set. bench/live_stage_matrix.sh sets it together with
PYTHONPATH=bench/stagetime, so every vLLM process (API servers, EngineCore) imports this file at start-up. Each target
below is wrapped right after its module is imported, and every call appends one JSON line to
$STAGE_TIMING_DIR/<pid>.jsonl:
  stage, pid, title (process title), ts (wall-clock start), wall (s), tcpu (calling thread's CPU s),
  pcpu (whole-process CPU s), plus per-stage extras.
tcpu misses native worker threads (FFmpeg/PyAV, NVDEC driver); pcpu includes them but also any concurrent request, so
read pcpu only from sequential runs. GPU stages are timed with CUDA events (no added synchronization) and carry "gpu".

Table stage -> records: 1 download | 2 remux | 3 nvdec_probe + nvdec_decode, or opencv_open + opencv_read |
4 d2h | 5 video_resize_norm (inside video_preprocess) | 6 fetch_audio (download + audio_decode), audio_resample,
audio_mel | frontend totals: render_messages, process_for_engine (= mm thread queue + mm_process), mm_hash,
msgpack_encode | 7 encoder (encoder_video, encoder_audio) | 8, 9 request (vLLM's per-request prefill/decode times).
"""
import os

if os.environ.get("STAGE_TIMING_DIR"):
    import functools, importlib.abc, inspect, json, sys, threading, time

    _DIR = os.environ["STAGE_TIMING_DIR"]
    _lock = threading.Lock()
    _tl = threading.local()
    _out = {"pid": None, "f": None}

    def _title():
        try:
            return open("/proc/self/cmdline", "rb").read().split(b"\0")[0].decode(errors="replace")[:48]
        except OSError:
            return "?"

    def _write(rec):
        rec.setdefault("pid", os.getpid())
        rec["title"] = _title()
        line = json.dumps(rec, default=str) + "\n"
        with _lock:
            if _out["pid"] != os.getpid():
                _out["f"] = open(os.path.join(_DIR, f"{os.getpid()}.jsonl"), "a", buffering=1)
                _out["pid"] = os.getpid()
            _out["f"].write(line)

    def _timed(stage, extra=None):
        """Wrap a sync or async callable; extra(args, kwargs, result) -> dict of fields, or None to skip the record."""

        def make(fn):
            if inspect.iscoroutinefunction(fn):

                @functools.wraps(fn)
                async def aw(*a, **k):
                    ts, t0 = time.time(), time.perf_counter()
                    rec = {"stage": stage, "ts": ts}
                    try:
                        out = await fn(*a, **k)
                    except BaseException as e:
                        rec.update(wall=time.perf_counter() - t0, err=type(e).__name__)
                        _write(rec)
                        raise
                    rec["wall"] = time.perf_counter() - t0
                    more = extra(a, k, out) if extra else {}
                    if more is not None:
                        rec.update(more)
                        _write(rec)
                    return out

                return aw

            @functools.wraps(fn)
            def w(*a, **k):
                ts, t0, c0, p0 = time.time(), time.perf_counter(), time.thread_time(), time.process_time()
                rec = {"stage": stage, "ts": ts}
                try:
                    out = fn(*a, **k)
                except BaseException as e:
                    rec.update(wall=time.perf_counter() - t0, tcpu=time.thread_time() - c0,
                               pcpu=time.process_time() - p0, err=type(e).__name__)
                    _write(rec)
                    raise
                rec.update(wall=time.perf_counter() - t0, tcpu=time.thread_time() - c0, pcpu=time.process_time() - p0)
                more = extra(a, k, out) if extra else {}
                if more is not None:
                    rec.update(more)
                    _write(rec)
                return out

            return w

        return make

    # --- GPU stages: CUDA events, resolved by a poller thread so the engine loop never blocks on them.
    _pending, _plock = [], threading.Lock()

    def _flush_gpu():
        with _plock:
            while _pending and _pending[0][1].query():
                s, e, rec = _pending.pop(0)
                rec["gpu"] = s.elapsed_time(e) / 1000.0
                _write(rec)

    def _poll_gpu():
        while True:
            time.sleep(0.5)
            try:
                _flush_gpu()
            except Exception as e:  # never let the poller die silently
                _write({"stage": "_gpu_poll_error", "err": repr(e)})

    _poller = {"started": False}

    def _gpu_timed(stage, extra=None):
        def make(fn):
            @functools.wraps(fn)
            def w(*a, **k):
                import torch

                if not _poller["started"]:
                    _poller["started"] = True
                    threading.Thread(target=_poll_gpu, daemon=True).start()
                more = extra(a, k) if extra else {}
                if more is None:
                    return fn(*a, **k)
                s, e = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
                ts, t0, c0 = time.time(), time.perf_counter(), time.thread_time()
                s.record()
                out = fn(*a, **k)
                e.record()
                rec = {"stage": stage, "ts": ts, "wall": time.perf_counter() - t0, "tcpu": time.thread_time() - c0, **more}
                with _plock:
                    _pending.append((s, e, rec))
                return out

            return w

        return make

    def _encoder_items(a, k):
        runner, sched = a[0], a[1]
        enc = getattr(sched, "scheduled_encoder_inputs", None) or {}
        if not enc:
            return None
        mods = []
        for rid, idxs in enc.items():
            try:
                feats = runner.requests[rid].mm_features
                mods += [feats[i].modality for i in idxs]
            except Exception:
                mods.append("?")
        return {"n_items": len(mods), "n_reqs": len(enc), "modalities": mods}

    # --- NVDEC decode vs device->host copy split: _pynvvc_frames_to_nhwc marks the end of decode (+ stack/permute
    # launch) inside _decode_to_pinned_host; the rest (pinned alloc, copy_, stream.synchronize) is the host copy.
    def _nhwc_mark(fn):
        @functools.wraps(fn)
        def w(*a, **k):
            out = fn(*a, **k)
            _tl.nhwc = (time.perf_counter(), time.thread_time())
            return out

        return w

    def _decode_to_host(fn):
        @functools.wraps(fn)
        def w(*a, **k):
            _tl.nhwc = None
            ts, t0, c0 = time.time(), time.perf_counter(), time.thread_time()
            out = fn(*a, **k)
            t1, c1 = time.perf_counter(), time.thread_time()
            m = getattr(_tl, "nhwc", None)
            if m is not None:
                n = len(a[2]) if len(a) > 2 else None
                _write({"stage": "nvdec_decode", "ts": ts, "wall": m[0] - t0, "tcpu": m[1] - c0, "frames": n})
                _write({"stage": "d2h", "ts": ts + (m[0] - t0), "wall": t1 - m[0], "tcpu": c1 - m[1],
                        "bytes": getattr(out, "nbytes", None)})
            return out

        return w

    def _finished(fn):
        @functools.wraps(fn)
        def w(self, *a, **k):
            out = fn(self, *a, **k)
            try:
                f = self.finished_requests[-1]
                _write({"stage": "request", "ts": time.time(), "request_id": f.request_id, "e2e": f.e2e_latency,
                        "queued": f.queued_time, "prefill": f.prefill_time, "decode": f.decode_time,
                        "inference": f.inference_time, "tpot": f.mean_time_per_output_token,
                        "prompt_tokens": f.num_prompt_tokens, "gen_tokens": f.num_generation_tokens,
                        "cached_tokens": f.num_cached_tokens})
            except Exception as e:
                _write({"stage": "_request_error", "err": repr(e)})
            return out

        return w

    def _shape(x):
        return list(getattr(x, "shape", []) or [])

    _TARGETS = {
        "vllm.connections": [
            ("HTTPConnection.async_get_bytes", _timed("download", lambda a, k, o: {"bytes": len(o)})),
        ],
        "vllm.multimodal.media.connector": [
            ("MediaConnector.fetch_video_async", _timed("fetch_video")),
            ("MediaConnector.fetch_audio_async", _timed("fetch_audio")),
        ],
        "vllm.multimodal.video": [
            ("_remux_mpegts_to_mp4", _timed("remux", lambda a, k, o: {"bytes_in": len(a[0]), "bytes_out": len(o)})),
            ("VideoBackend.load_bytes", _timed("video_decode_total",
                                               lambda a, k, o: {"backend": k.get("backend"), "frames": _shape(o[0])})),
            ("PyNvVideoCodecVideoBackendMixin._read_source_metadata", _timed("nvdec_probe")),
            ("PyNvVideoCodecVideoBackendMixin._decode_to_pinned_host", _decode_to_host),
            ("_pynvvc_frames_to_nhwc", _nhwc_mark),
            ("OpenCVVideoBackendMixin.open_video_capture", _timed("opencv_open")),
            ("OpenCVVideoBackendMixin.read_frames", _timed("opencv_read")),
        ],
        "vllm.multimodal.media.audio": [
            ("AudioMediaIO.load_bytes", _timed("audio_decode", lambda a, k, o: {"samples": len(o[0]), "sr": o[1]})),
            ("load_audio_soundfile", _timed("audio_decode_soundfile")),
            ("load_audio_pyav", _timed("audio_decode_pyav")),
        ],
        "vllm.multimodal.audio": [
            ("AudioResampler.resample", _timed("audio_resample", lambda a, k, o: {"orig_sr": k.get("orig_sr"),
                                                                                  "samples_out": len(o)})),
        ],
        "vllm.model_executor.models.parakeet": [
            ("ParakeetExtractor.__call__", _timed("audio_mel")),
        ],
        "vllm.transformers_utils.processors.nano_nemotron_vl": [
            ("video_to_pixel_values", _timed("video_resize_norm",
                                             lambda a, k, o: {"in": _shape(a[0]), "out": _shape(o), "dtype": o.dtype})),
            ("NanoNemotronVLProcessor._preprocess_video", _timed("video_preprocess")),
            ("NanoNemotronVLProcessor._preprocess_audio", _timed("audio_preprocess")),
            ("NanoNemotronVLProcessor.__call__", _timed("hf_processor")),
        ],
        "vllm.renderers.hf": [
            ("HfRenderer.render_messages_async", _timed("render_messages")),
        ],
        "vllm.renderers.base": [
            ("BaseRenderer.process_for_engine_async", _timed("process_for_engine")),
            ("BaseRenderer._process_multimodal", _timed("mm_process")),
        ],
        "vllm.multimodal.hasher": [
            ("MultiModalHasher.hash_kwargs", _timed("mm_hash")),
        ],
        "vllm.v1.serial_utils": [
            ("MsgpackEncoder.encode", _timed("msgpack_encode", lambda a, k, o: (
                {"bytes": n} if (n := sum(memoryview(b).nbytes for b in o)) >= 1 << 20 else None))),
        ],
        "vllm.v1.metrics.stats": [
            ("IterationStats.update_from_finished_request", _finished),
        ],
        "vllm.v1.worker.gpu_model_runner": [
            ("GPUModelRunner._execute_mm_encoder", _gpu_timed("encoder", _encoder_items)),
        ],
        "vllm.model_executor.models.nano_nemotron_vl": [
            ("NemotronH_Nano_VL_V2._process_video_input", _gpu_timed("encoder_video")),
            ("NemotronH_Nano_VL_V2._process_audio_input", _gpu_timed("encoder_audio")),
        ],
    }

    def _patch(module, path, make):
        *owner_path, name = path.split(".")
        owner = module
        for p in owner_path:
            owner = getattr(owner, p)
        if isinstance(owner, type):
            owner = next(c for c in owner.__mro__ if name in c.__dict__)
            raw = owner.__dict__[name]
            if isinstance(raw, (classmethod, staticmethod)):
                setattr(owner, name, type(raw)(make(raw.__func__)))
            else:
                setattr(owner, name, make(raw))
        else:
            setattr(owner, name, make(getattr(owner, name)))

    class _Finder(importlib.abc.MetaPathFinder):
        def find_spec(self, name, path=None, target=None):
            if name not in _TARGETS:
                return None
            for finder in sys.meta_path:
                if finder is self or not hasattr(finder, "find_spec"):
                    continue
                spec = finder.find_spec(name, path, target)
                if spec is not None:
                    break
            else:
                return None
            exec_module = spec.loader.exec_module

            def exec_and_patch(module):
                exec_module(module)
                done, failed = [], []
                for p, make in _TARGETS[name]:
                    try:
                        _patch(module, p, make)
                        done.append(p)
                    except Exception as e:
                        failed.append(f"{p}: {e!r}")
                _write({"stage": "_patched", "ts": time.time(), "module": name, "done": done, "failed": failed})

            spec.loader.exec_module = exec_and_patch
            return spec

    sys.meta_path.insert(0, _Finder())
