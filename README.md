# LLM inference on FPGA papers

This repository is a local research survey of arXiv-hosted papers concerning
LLM inference on FPGAs. `data/catalog.json` and `data/survey.csv` are tracked;
`papers/` is an ignored local research cache and must not be re-hosted.

## Commands

```sh
python3 scripts/collect_arxiv.py bootstrap --all --download
python3 scripts/collect_arxiv.py sync --download-new
python3 scripts/collect_arxiv.py render
python3 scripts/install_cron.py --install
```

The collector serializes arXiv API calls at least three seconds apart. See the
arXiv API manual at https://info.arxiv.org/help/api/user-manual.html and the
terms of use at https://info.arxiv.org/help/api/tou.html. Public availability
does not itself grant redistribution rights for a PDF.

## Survey

| Paper | Submitted | Updated | Categories | Status | Quantization | Architecture | FPGA | Model | Toolflow | Evidence | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [Multi-Level Resistive Synapses for On-Chip Neural Networks: A Physics-Based Design of a Memristive Crossbar Fabric with Quasi-Continuous Conductance States](https://arxiv.org/abs/2606.22621v1) ([PDF](https://arxiv.org/pdf/2606.22621v1)) | 2026-06-21T18:04:51Z | 2026-06-21T18:04:51Z | cs.AR, cond-mat.mes-hall, cs.ET, cs.NE, physics.app-ph |  |  |  |  |  |  |  |  |
| [ITME: Inference Tiered Memory Expansion with Disaggregated CXL-Hybrid Memories](https://arxiv.org/abs/2606.12556v2) ([PDF](https://arxiv.org/pdf/2606.12556v2)) | 2026-06-10T18:06:30Z | 2026-06-16T05:18:15Z | cs.DC |  |  |  |  |  |  |  |  |
| [Tiara: A Programmable Line-Rate ISA for Remote Memory Access](https://arxiv.org/abs/2606.13708v1) ([PDF](https://arxiv.org/pdf/2606.13708v1)) | 2026-06-10T05:01:17Z | 2026-06-10T05:01:17Z | cs.AR, cs.NI |  |  |  |  |  |  |  |  |
| [Understand and Accelerate Memory Processing Pipeline for Large Language Model Inference](https://arxiv.org/abs/2603.29002v3) ([PDF](https://arxiv.org/pdf/2603.29002v3)) | 2026-03-30T21:03:39Z | 2026-05-30T00:45:53Z | cs.DC, cs.AI |  |  |  |  |  |  |  |  |
| [XtraMAC: An Efficient MAC Architecture for Mixed-Precision LLM Inference on FPGA](https://arxiv.org/abs/2605.06052v1) ([PDF](https://arxiv.org/pdf/2605.06052v1)) | 2026-05-07T11:37:52Z | 2026-05-07T11:37:52Z | cs.AR |  |  |  |  |  |  |  |  |
| [Design Conductor 2.0: An agent builds a TurboQuant inference accelerator in 80 hours](https://arxiv.org/abs/2605.05170v1) ([PDF](https://arxiv.org/pdf/2605.05170v1)) | 2026-05-06T17:40:03Z | 2026-05-06T17:40:03Z | cs.AR, cs.AI |  |  |  |  |  |  |  |  |
| [A Switch-Centric In-Network Architecture for Accelerating LLM Inference in Shared-Memory Network](https://arxiv.org/abs/2603.28239v3) ([PDF](https://arxiv.org/pdf/2603.28239v3)) | 2026-03-30T09:59:11Z | 2026-04-08T07:25:22Z | cs.AR |  |  |  |  |  |  |  |  |
| [HillInfer: Efficient Long-Context LLM Inference on the Edge with Hierarchical KV Eviction using SmartSSD](https://arxiv.org/abs/2602.18750v2) ([PDF](https://arxiv.org/pdf/2602.18750v2)) | 2026-02-21T08:19:59Z | 2026-03-25T06:46:30Z | cs.AR |  |  |  |  |  |  |  |  |
| [Energy Efficient Software Hardware CoDesign for Machine Learning: From TinyML to Large Language Models](https://arxiv.org/abs/2603.23668v1) ([PDF](https://arxiv.org/pdf/2603.23668v1)) | 2026-03-24T19:10:42Z | 2026-03-24T19:10:42Z | cs.AR, cs.LG |  |  |  |  |  |  |  |  |
| [LUT-LLM: Efficient Large Language Model Inference with Memory-based Computations on FPGAs](https://arxiv.org/abs/2511.06174v2) ([PDF](https://arxiv.org/pdf/2511.06174v2)) | 2025-11-09T01:17:08Z | 2026-03-22T06:32:51Z | cs.AR, cs.AI |  |  |  |  |  |  |  |  |
| [SkipOPU: An FPGA-based Overlay Processor for Large Language Models with Dynamically Allocated Computation](https://arxiv.org/abs/2603.14785v1) ([PDF](https://arxiv.org/pdf/2603.14785v1)) | 2026-03-16T03:35:04Z | 2026-03-16T03:35:04Z | cs.AR |  |  |  |  |  |  |  |  |
| [FAST-Prefill: FPGA Accelerated Sparse Attention for Long Context LLM Prefill](https://arxiv.org/abs/2602.20515v1) ([PDF](https://arxiv.org/pdf/2602.20515v1)) | 2026-02-24T03:36:25Z | 2026-02-24T03:36:25Z | cs.AR |  |  |  |  |  |  |  |  |
| [FlexLLM: Composable HLS Library for Flexible Hybrid LLM Accelerator Design](https://arxiv.org/abs/2601.15710v1) ([PDF](https://arxiv.org/pdf/2601.15710v1)) | 2026-01-22T07:31:51Z | 2026-01-22T07:31:51Z | cs.AR, cs.AI, cs.LG |  |  |  |  |  |  |  |  |
| [FPGA Co-Design for Efficient N:M Sparse and Quantized Model Inference](https://arxiv.org/abs/2512.24713v2) ([PDF](https://arxiv.org/pdf/2512.24713v2)) | 2025-12-31T08:27:40Z | 2026-01-20T14:13:05Z | cs.LG, cs.AR |  |  |  |  |  |  |  |  |
| [Hardware Acceleration for Neural Networks: A Comprehensive Survey](https://arxiv.org/abs/2512.23914v3) ([PDF](https://arxiv.org/pdf/2512.23914v3)) | 2025-12-30T00:27:02Z | 2026-01-15T06:37:21Z | eess.SY |  |  |  |  |  |  |  |  |
| [HPU: High-Bandwidth Processing Unit for Scalable, Cost-effective LLM Inference via GPU Co-processing](https://arxiv.org/abs/2504.16112v2) ([PDF](https://arxiv.org/pdf/2504.16112v2)) | 2025-04-18T03:31:08Z | 2025-12-17T21:40:17Z | cs.AR, cs.AI, cs.CL, cs.DC |  |  |  |  |  |  |  |  |
| [PD-Swap: Prefill-Decode Logic Swapping for End-to-End LLM Inference on Edge FPGAs via Dynamic Partial Reconfiguration](https://arxiv.org/abs/2512.11550v1) ([PDF](https://arxiv.org/pdf/2512.11550v1)) | 2025-12-12T13:35:09Z | 2025-12-12T13:35:09Z | cs.AR |  |  |  |  |  |  |  |  |
| [Efficient Kernel Mapping and Comprehensive System Evaluation of LLM Acceleration on a CGLA](https://arxiv.org/abs/2512.00335v1) ([PDF](https://arxiv.org/pdf/2512.00335v1)) | 2025-11-29T05:55:37Z | 2025-11-29T05:55:37Z | cs.AR |  |  |  |  |  |  |  |  |
| [T-SAR: A Full-Stack Co-design for CPU-Only Ternary LLM Inference via In-Place SIMD ALU Reorganization](https://arxiv.org/abs/2511.13676v1) ([PDF](https://arxiv.org/pdf/2511.13676v1)) | 2025-11-17T18:32:03Z | 2025-11-17T18:32:03Z | cs.AR, cs.LG |  |  |  |  |  |  |  |  |
| [TeLLMe v2: An Efficient End-to-End Ternary LLM Prefill and Decode Accelerator with Table-Lookup Matmul on Edge FPGAs](https://arxiv.org/abs/2510.15926v2) ([PDF](https://arxiv.org/pdf/2510.15926v2)) | 2025-10-03T05:37:51Z | 2025-10-21T17:20:02Z | cs.AR, cs.LG |  |  |  |  |  |  |  |  |
| [Architect in the Loop Agentic Hardware Design and Verification](https://arxiv.org/abs/2512.00016v1) ([PDF](https://arxiv.org/pdf/2512.00016v1)) | 2025-10-19T22:30:28Z | 2025-10-19T22:30:28Z | cs.AR, cs.AI, cs.LG |  |  |  |  |  |  |  |  |
| [FourierCompress: Layer-Aware Spectral Activation Compression for Efficient and Accurate Collaborative LLM Inference](https://arxiv.org/abs/2510.16418v1) ([PDF](https://arxiv.org/pdf/2510.16418v1)) | 2025-10-18T09:26:02Z | 2025-10-18T09:26:02Z | cs.DC |  |  |  |  |  |  |  |  |
| [Hummingbird: A Smaller and Faster Large Language Model Accelerator on Embedded FPGA](https://arxiv.org/abs/2507.03308v2) ([PDF](https://arxiv.org/pdf/2507.03308v2)) | 2025-07-04T05:35:19Z | 2025-10-17T12:09:13Z | cs.AR |  |  |  |  |  |  |  |  |
| [LightMamba: Efficient Mamba Acceleration on FPGA with Quantization and Hardware Co-design](https://arxiv.org/abs/2502.15260v2) ([PDF](https://arxiv.org/pdf/2502.15260v2)) | 2025-02-21T07:23:23Z | 2025-10-10T11:26:17Z | cs.CL |  |  |  |  |  |  |  |  |
| [CMOS Implementation of Field Programmable Spiking Neural Network for Hardware Reservoir Computing](https://arxiv.org/abs/2509.17355v1) ([PDF](https://arxiv.org/pdf/2509.17355v1)) | 2025-09-22T05:19:46Z | 2025-09-22T05:19:46Z | cs.NE |  |  |  |  |  |  |  |  |
| [TENET: An Efficient Sparsity-Aware LUT-Centric Architecture for Ternary LLM Inference On Edge](https://arxiv.org/abs/2509.13765v1) ([PDF](https://arxiv.org/pdf/2509.13765v1)) | 2025-09-17T07:24:25Z | 2025-09-17T07:24:25Z | cs.AR |  |  |  |  |  |  |  |  |
| [DiffAxE: Diffusion-driven Hardware Accelerator Generation and Design Space Exploration](https://arxiv.org/abs/2508.10303v1) ([PDF](https://arxiv.org/pdf/2508.10303v1)) | 2025-08-14T03:19:34Z | 2025-08-14T03:19:34Z | cs.AR |  |  |  |  |  |  |  |  |
| [Investigating 1-Bit Quantization in Transformer-Based Top Tagging](https://arxiv.org/abs/2508.07431v1) ([PDF](https://arxiv.org/pdf/2508.07431v1)) | 2025-08-10T17:06:24Z | 2025-08-10T17:06:24Z | hep-ph |  |  |  |  |  |  |  |  |
| [Research on Low-Latency Inference and Training Efficiency Optimization for Graph Neural Network and Large Language Model-Based Recommendation Systems](https://arxiv.org/abs/2507.01035v1) ([PDF](https://arxiv.org/pdf/2507.01035v1)) | 2025-06-21T03:10:50Z | 2025-06-21T03:10:50Z | cs.LG, cs.AI, cs.PF |  |  |  |  |  |  |  |  |
| [Large Language Model Inference Acceleration: A Comprehensive Hardware Perspective](https://arxiv.org/abs/2410.04466v4) ([PDF](https://arxiv.org/pdf/2410.04466v4)) | 2024-10-06T12:42:04Z | 2025-06-13T12:20:54Z | cs.AR, cs.LG |  |  |  |  |  |  |  |  |
| [Design and Implementation of an FPGA-Based Hardware Accelerator for Transformer](https://arxiv.org/abs/2503.16731v3) ([PDF](https://arxiv.org/pdf/2503.16731v3)) | 2025-03-20T22:15:42Z | 2025-05-20T20:28:55Z | cs.AR, cs.CL, cs.LG |  |  |  |  |  |  |  |  |
| [SpeedLLM: An FPGA Co-design of Large Language Model Inference Accelerator](https://arxiv.org/abs/2507.14139v1) ([PDF](https://arxiv.org/pdf/2507.14139v1)) | 2025-05-07T05:39:07Z | 2025-05-07T05:39:07Z | cs.AR |  |  |  |  |  |  |  |  |
| [TerEffic: Highly Efficient Ternary LLM Inference on FPGA](https://arxiv.org/abs/2502.16473v2) ([PDF](https://arxiv.org/pdf/2502.16473v2)) | 2025-02-23T07:16:51Z | 2025-05-01T05:05:03Z | cs.AR |  |  |  |  |  |  |  |  |
| [TeLLMe: An Energy-Efficient Ternary LLM Accelerator for Prefilling and Decoding on Edge FPGAs](https://arxiv.org/abs/2504.16266v2) ([PDF](https://arxiv.org/pdf/2504.16266v2)) | 2025-04-22T21:00:58Z | 2025-04-24T18:14:11Z | cs.AR, cs.LG |  |  |  |  |  |  |  |  |
| [On-Device Qwen2.5: Efficient LLM Inference with Model Compression and Hardware Acceleration](https://arxiv.org/abs/2504.17376v1) ([PDF](https://arxiv.org/pdf/2504.17376v1)) | 2025-04-24T08:50:01Z | 2025-04-24T08:50:01Z | cs.AR, cs.LG |  |  |  |  |  |  |  |  |
| [LoopLynx: A Scalable Dataflow Architecture for Efficient LLM Inference](https://arxiv.org/abs/2504.09561v1) ([PDF](https://arxiv.org/pdf/2504.09561v1)) | 2025-04-13T13:23:14Z | 2025-04-13T13:23:14Z | cs.AR |  |  |  |  |  |  |  |  |
| [AccLLM: Accelerating Long-Context LLM Inference Via Algorithm-Hardware Co-Design](https://arxiv.org/abs/2505.03745v1) ([PDF](https://arxiv.org/pdf/2505.03745v1)) | 2025-04-07T02:52:30Z | 2025-04-07T02:52:30Z | cs.AR, cs.AI, cs.LG |  |  |  |  |  |  |  |  |
| [Chameleon: a Heterogeneous and Disaggregated Accelerator System for Retrieval-Augmented Language Models](https://arxiv.org/abs/2310.09949v4) ([PDF](https://arxiv.org/pdf/2310.09949v4)) | 2023-10-15T20:57:25Z | 2025-03-24T18:01:48Z | cs.LG, cs.AI, cs.AR, cs.CL |  |  |  |  |  |  |  |  |
| [Pushing up to the Limit of Memory Bandwidth and Capacity Utilization for Efficient LLM Decoding on Embedded FPGA](https://arxiv.org/abs/2502.10659v1) ([PDF](https://arxiv.org/pdf/2502.10659v1)) | 2025-02-15T03:56:22Z | 2025-02-15T03:56:22Z | cs.AR |  |  |  |  |  |  |  |  |
| [Pushing the Limits of BFP on Narrow Precision LLM Inference](https://arxiv.org/abs/2502.00026v2) ([PDF](https://arxiv.org/pdf/2502.00026v2)) | 2025-01-21T17:10:52Z | 2025-02-07T12:23:59Z | cs.AR, cs.AI |  |  |  |  |  |  |  |  |
| [A Tensor-Train Decomposition based Compression of LLMs on Group Vector Systolic Accelerator](https://arxiv.org/abs/2501.19135v1) ([PDF](https://arxiv.org/pdf/2501.19135v1)) | 2025-01-31T13:45:31Z | 2025-01-31T13:45:31Z | cs.AR |  |  |  |  |  |  |  |  |
| [Real-world Edge Neural Network Implementations Leak Private Interactions Through Physical Side Channel](https://arxiv.org/abs/2501.14512v1) ([PDF](https://arxiv.org/pdf/2501.14512v1)) | 2025-01-24T14:15:51Z | 2025-01-24T14:15:51Z | cs.CR |  |  |  |  |  |  |  |  |
| [IANUS: Integrated Accelerator based on NPU-PIM Unified Memory System](https://arxiv.org/abs/2410.15008v1) ([PDF](https://arxiv.org/pdf/2410.15008v1)) | 2024-10-19T06:43:20Z | 2024-10-19T06:43:20Z | cs.AR |  |  |  |  |  |  |  |  |
| [SeedLM: Compressing LLM Weights into Seeds of Pseudo-Random Generators](https://arxiv.org/abs/2410.10714v2) ([PDF](https://arxiv.org/pdf/2410.10714v2)) | 2024-10-14T16:57:23Z | 2024-10-16T00:11:57Z | cs.LG, cs.AI |  |  |  |  |  |  |  |  |
| [LlamaF: An Efficient Llama2 Architecture Accelerator on Embedded FPGAs](https://arxiv.org/abs/2409.11424v1) ([PDF](https://arxiv.org/pdf/2409.11424v1)) | 2024-09-12T17:53:37Z | 2024-09-12T17:53:37Z | cs.AR |  |  |  |  |  |  |  |  |
| [Research on LLM Acceleration Using the High-Performance RISC-V Processor "Xiangshan" (Nanhu Version) Based on the Open-Source Matrix Instruction Set Extension (Vector Dot Product)](https://arxiv.org/abs/2409.00661v1) ([PDF](https://arxiv.org/pdf/2409.00661v1)) | 2024-09-01T08:27:00Z | 2024-09-01T08:27:00Z | cs.AR |  |  |  |  |  |  |  |  |
| [Designing Efficient LLM Accelerators for Edge Devices](https://arxiv.org/abs/2408.00462v1) ([PDF](https://arxiv.org/pdf/2408.00462v1)) | 2024-08-01T11:06:05Z | 2024-08-01T11:06:05Z | cs.AR, cs.LG |  |  |  |  |  |  |  |  |
| [HLSTransform: Energy-Efficient Llama 2 Inference on FPGAs Via High Level Synthesis](https://arxiv.org/abs/2405.00738v1) ([PDF](https://arxiv.org/pdf/2405.00738v1)) | 2024-04-29T21:26:06Z | 2024-04-29T21:26:06Z | cs.AR, cs.AI, cs.LG |  |  |  |  |  |  |  |  |
| [Understanding the Potential of FPGA-Based Spatial Acceleration for Large Language Model Inference](https://arxiv.org/abs/2312.15159v2) ([PDF](https://arxiv.org/pdf/2312.15159v2)) | 2023-12-23T04:27:06Z | 2024-04-07T06:03:02Z | cs.LG, cs.AI, cs.AR, cs.CL |  |  |  |  |  |  |  |  |
| [FlightLLM: Efficient Large Language Model Inference with a Complete Mapping Flow on FPGAs](https://arxiv.org/abs/2401.03868v2) ([PDF](https://arxiv.org/pdf/2401.03868v2)) | 2024-01-08T13:00:53Z | 2024-01-09T06:47:46Z | cs.AR, cs.AI |  |  |  |  |  |  |  |  |
