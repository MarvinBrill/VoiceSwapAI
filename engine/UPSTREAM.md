# RVC engine provenance

Source: https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI

Vendored from the user's local checkout at commit
`81eed5e8f68b6bed1789f682fe78cdd324495afc` on 2026-10-24.
The source repository is unchanged. The MIT license is retained in `rvc/LICENSE`.

VoiceSwapAI uses the RVC synthesizers, HuBERT/ContentVec adapter, RMVPE, FCPE,
retrieval inference pipeline and adversarial trainer. The upstream Gradio app,
desktop GUI and VST project are not part of the application.

Local adaptations:

- Device configuration without CLI parsing: CUDA/ROCm, Intel XPU, Windows DirectML and CPU.
- Single-device training with `.to(device)`; FP32 training for stability.
- Persistent data/weight directories from environment variables.
- HuBERT path and translations resolved independently of the current directory.
- Training sampler includes short clips; preprocessing writes PCM16 training WAVs.
- Atomic epoch progress reporting for the web queue.
- Floating-point inference output and overlapping crossfades before 24-bit export.
- Inference receives validated model files through a separate adapter.
- DirectML uses FP32, no_grad instead of inference_mode, differentiable CPU FFT
  and relative-position rearrangement, CPU-portable checkpoints, and positive
  padding followed by cropping in the sine generator. RMVPE keeps its convolutional
  network on DirectML and its unsupported GRU/spectral preprocessing on CPU.

Dataset preprocessing, feature extraction orchestration, streaming conversion,
asset installation, model library and job management live in `backend/app`.

`assets.json` locks official Hugging Face assets to a specific repository revision,
byte size and SHA-256 digest. Downloads are never executed as programs.
The pinned RVC branch requires PyTorch <2.8 with matching torchaudio; the application
uses PyTorch 2.7.1/CUDA 12.8 for NVIDIA Blackwell compatibility. The separate native
Windows DirectML environment uses PyTorch 2.4.1 as required by Microsoft's plugin.
User voice weights are admitted only as non-TorchScript ZIP checkpoints and read
with weights_only=True; the unsafe legacy-TAR path of older PyTorch is never used.

Additional components: Hybrid Demucs 4.0.1 (MIT) via the Python distribution,
FFmpeg via Debian, React (MIT), Lucide (ISC), DM Sans and Manrope (OFL) bundled
locally through Fontsource. Their upstream distributions retain their licenses.
