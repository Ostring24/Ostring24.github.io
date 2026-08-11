---
title: "Qwen3-next 模型DeepDive"
date: 2026-08-11T15:40:32+08:00
lastmod: 2026-08-11T15:40:32+08:00
summary: "拆解 Qwen3-Next-80B-A3B 的混合架构：Gated DeltaNet 线性注意力与标准注意力交替、MoE 稀疏层，以及 solve_tril 三角求逆算子的分层实现。"
draft: false
aliases: ["/posts/model/qwen3_next_80b_a3b_deepdive/"]
tags: ["Qwen", "MoE", "模型结构", "推理优化"]
private: true
build:
  list: never
  render: never
---

# model 结构

```python
Qwen3NextModel(
  (embed_tokens): VocabParallelEmbedding(num_embeddings=18992, embedding_dim=2048, org_vocab_size=151936, num_embeddings_padded=151936, tp_size=8)
  (layers): ModuleList(
    (0-2): 3 x Qwen3HybridLinearDecoderLayer(
      (linear_attn): Qwen3GatedDeltaNet(
        (conv1d): ColumnParallelLinear(in_features=4, output_features=1024, bias=False, tp_size=8, gather_output=False)
        (in_proj_qkvz): ColumnParallelLinear(in_features=2048, output_features=1536, bias=False, tp_size=8, gather_output=False)
        (in_proj_ba): ColumnParallelLinear(in_features=2048, output_features=8, bias=False, tp_size=8, gather_output=False)
        (norm): RMSNorm()
        (out_proj): RowParallelLinear(input_features=512, output_features=2048, bias=False, tp_size=8, reduce_results=False)
      )
      (mlp): Qwen2MoeSparseMoeBlock(
        (topk): TopK()
        (experts): FusedMoE(
          (quant_method): UnquantizedFusedMoEMethod()
        )
        (gate): ReplicatedLinear(in_features=2048, output_features=512, bias=False)
        (shared_expert): Qwen2MoeMLP(
          (gate_up_proj): MergedColumnParallelLinear(in_features=2048, output_features=128, bias=False, tp_size=8, gather_output=False)
          (down_proj): RowParallelLinear(input_features=64, output_features=2048, bias=False, tp_size=8, reduce_results=False)
          (act_fn): SiluAndMul()
        )
        (shared_expert_gate): Linear(in_features=2048, out_features=1, bias=False)
      )
      (input_layernorm): GemmaRMSNorm()
      (post_attention_layernorm): GemmaRMSNorm()
    )
    (3): Qwen3HybridAttentionDecoderLayer(
      (rotary_emb): RotaryEmbedding(head_size=256, rotary_dim=64, max_position_embeddings=262144, base=10000000, is_neox_style=True)
      (qkv_proj): QKVParallelLinear(in_features=2048, output_features=1536, bias=False, tp_size=8, gather_output=False)
      (o_proj): RowParallelLinear(input_features=512, output_features=2048, bias=False, tp_size=8, reduce_results=False)
      (attn): RadixAttention()
      (mlp): Qwen2MoeSparseMoeBlock(
        (topk): TopK()
        (experts): FusedMoE(
          (quant_method): UnquantizedFusedMoEMethod()
        )
        (gate): ReplicatedLinear(in_features=2048, output_features=512, bias=False)
        (shared_expert): Qwen2MoeMLP(
          (gate_up_proj): MergedColumnParallelLinear(in_features=2048, output_features=128, bias=False, tp_size=8, gather_output=False)
          (down_proj): RowParallelLinear(input_features=64, output_features=2048, bias=False, tp_size=8, reduce_results=False)
          (act_fn): SiluAndMul()
        )
        (shared_expert_gate): Linear(in_features=2048, out_features=1, bias=False)
      )
      (input_layernorm): GemmaRMSNorm()
      (post_attention_layernorm): GemmaRMSNorm()
      (q_norm): GemmaRMSNorm()
      (k_norm): GemmaRMSNorm()
    )
    (4-6): 3 x Qwen3HybridLinearDecoderLayer(
      (linear_attn): Qwen3GatedDeltaNet(
        (conv1d): ColumnParallelLinear(in_features=4, output_features=1024, bias=False, tp_size=8, gather_output=False)
        (in_proj_qkvz): ColumnParallelLinear(in_features=2048, output_features=1536, bias=False, tp_size=8, gather_output=False)
        (in_proj_ba): ColumnParallelLinear(in_features=2048, output_features=8, bias=False, tp_size=8, gather_output=False)
        (norm): RMSNorm()
        (out_proj): RowParallelLinear(input_features=512, output_features=2048, bias=False, tp_size=8, reduce_results=False)
      )
      (mlp): Qwen2MoeSparseMoeBlock(
        (topk): TopK()
        (experts): FusedMoE(
          (quant_method): UnquantizedFusedMoEMethod()
        )
        (gate): ReplicatedLinear(in_features=2048, output_features=512, bias=False)
        (shared_expert): Qwen2MoeMLP(
          (gate_up_proj): MergedColumnParallelLinear(in_features=2048, output_features=128, bias=False, tp_size=8, gather_output=False)
          (down_proj): RowParallelLinear(input_features=64, output_features=2048, bias=False, tp_size=8, reduce_results=False)
          (act_fn): SiluAndMul()
        )
        (shared_expert_gate): Linear(in_features=2048, out_features=1, bias=False)
      )
      (input_layernorm): GemmaRMSNorm()
      (post_attention_layernorm): GemmaRMSNorm()
    )
......
    (44-46): 3 x Qwen3HybridLinearDecoderLayer(
      (linear_attn): Qwen3GatedDeltaNet(
        (conv1d): ColumnParallelLinear(in_features=4, output_features=1024, bias=False, tp_size=8, gather_output=False)
        (in_proj_qkvz): ColumnParallelLinear(in_features=2048, output_features=1536, bias=False, tp_size=8, gather_output=False)
        (in_proj_ba): ColumnParallelLinear(in_features=2048, output_features=8, bias=False, tp_size=8, gather_output=False)
        (norm): RMSNorm()
        (out_proj): RowParallelLinear(input_features=512, output_features=2048, bias=False, tp_size=8, reduce_results=False)
      )
      (mlp): Qwen2MoeSparseMoeBlock(
        (topk): TopK()
        (experts): FusedMoE(
          (quant_method): UnquantizedFusedMoEMethod()
        )
        (gate): ReplicatedLinear(in_features=2048, output_features=512, bias=False)
        (shared_expert): Qwen2MoeMLP(
          (gate_up_proj): MergedColumnParallelLinear(in_features=2048, output_features=128, bias=False, tp_size=8, gather_output=False)
          (down_proj): RowParallelLinear(input_features=64, output_features=2048, bias=False, tp_size=8, reduce_results=False)
          (act_fn): SiluAndMul()
        )
        (shared_expert_gate): Linear(in_features=2048, out_features=1, bias=False)
      )
      (input_layernorm): GemmaRMSNorm()
      (post_attention_layernorm): GemmaRMSNorm()
    )
    (47): Qwen3HybridAttentionDecoderLayer(
      (rotary_emb): RotaryEmbedding(head_size=256, rotary_dim=64, max_position_embeddings=262144, base=10000000, is_neox_style=True)
      (qkv_proj): QKVParallelLinear(in_features=2048, output_features=1536, bias=False, tp_size=8, gather_output=False)
      (o_proj): RowParallelLinear(input_features=512, output_features=2048, bias=False, tp_size=8, reduce_results=False)
      (attn): RadixAttention()
      (mlp): Qwen2MoeSparseMoeBlock(
        (topk): TopK()
        (experts): FusedMoE(
          (quant_method): UnquantizedFusedMoEMethod()
        )
        (gate): ReplicatedLinear(in_features=2048, output_features=512, bias=False)
        (shared_expert): Qwen2MoeMLP(
          (gate_up_proj): MergedColumnParallelLinear(in_features=2048, output_features=128, bias=False, tp_size=8, gather_output=False)
          (down_proj): RowParallelLinear(input_features=64, output_features=2048, bias=False, tp_size=8, reduce_results=False)
          (act_fn): SiluAndMul()
        )
        (shared_expert_gate): Linear(in_features=2048, out_features=1, bias=False)
      )
      (input_layernorm): GemmaRMSNorm()
      (post_attention_layernorm): GemmaRMSNorm()
      (q_norm): GemmaRMSNorm()
      (k_norm): GemmaRMSNorm()
    )
  )
  (norm): GemmaRMSNorm()
```

约 **75% layer 使用 Gated DeltaNet，25% layer 保留标准 Attention**。

总共48 layer, every 4 layer is a block, every block has 3 hybridLinearDecode layer, so:
total 36 conv1d op

Gated DeltaNet **不保存所有历史 K/V，而是把历史信息压缩到一个固定大小的 recurrent state 中。**最终只需要维护一个state，而不是线性增长的kv cache



qwen3

```

                  ┌───────────┐
Q ───────────────►│ Attention │
K ───────────────►│           │
V ───────────────►│           │
                  └─────┬─────┘
                        │
                        ▼
                    KV Cache
                        │
                        ▼
                  下一 token
```



qwen3-next

```
                   ┌────────────────┐
                   │ Gated DeltaNet │
                   └───────┬────────┘
                           │
                    recurrent state
                           │
                           ▼

                   ┌────────────────┐
                   │ Gated Attention│
                   └───────┬────────┘
                           │
                       KV Cache
```

> **Qwen3-Next 不是“没有 KV Cache”。**

而是：

> **只有一部分 Attention layer 需要传统 KV Cache；另外大部分 Gated DeltaNet layer 使用固定大小的 recurrent state。**



- 模型参数

80B total 3B active 48 layers 512 experts 10 activated experts 1 shared expert

# 模型整体性能

## prefill


|                                                                                                                                                                                                                                                               |      |              |         |            |          |      |     |           |                     |                  |         |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---- | ------------ | ------- | ---------- | -------- | ---- | --- | --------- | ------------------- | ---------------- | ------- |
| 名称                                                                                                                                                                                                                                                            | 开始时间 | 持续时间(ms)     | 百分比     | 平均时间       | op(ms)   | 数量   |     | gpu (ms)  | 65% gpu             | prefill 提升       | Comment |
| 总计                                                                                                                                                                                                                                                            |      | 654.511585ms | 100.00% | 0.168384ms | 0.168384 | 3887 |     |           |                     |                  |         |
| void slice_kernel<2, 2, (SlicePattern)3>(void*, void*, SliceParams)                                                                                                                                                                                           |      | 180.598013ms | 27.59%  | 0.501661ms | 0.501661 | 360  |     |           |                     |                  |         |
| merge_16x16_to_64x64_inverse_kernel                                                                                                                                                                                                                           |      | 107.461761ms | 16.42%  | 2.985048ms | 2.985048 | 36   |     | 0.00654   | 0.0100615384615385  | 107.099512615385 | 15% GPU |
| *causal*conv1d_fwd_kernel                                                                                                                                                                                                                                     |      | 96.795834ms  | 14.79%  | 2.688773ms | 2.688773 | 36   |     | 0.004588  | 0.00705846153846154 | 96.5417233846154 | topscc  |
| layer_norm_fwd_kernel                                                                                                                                                                                                                                         |      | 65.754480ms  | 10.05%  | 1.826513ms | 1.826513 | 36   |     | 0.0013911 | 0.00214015384615385 | 65.6774224615385 |         |
| chunk_gated_delta_rule_fwd_kernel_h_blockdim64                                                                                                                                                                                                                |      | 29.540215ms  | 4.51%   | 0.820561ms | 0.820561 | 36   |     | 0.051404  | 0.0790830769230769  | 26.6932052307692 |         |
| solve_tril_16x16_kernel                                                                                                                                                                                                                                       |      | 20.454462ms  | 3.13%   | 0.568179ms | 0.568179 | 36   |     | 0.006423  | 0.00988153846153846 | 20.0987086153846 |         |
| void invoke_fused_moe_kernel_m_cut_intra_die<(MultiCoreCutType)2, tops::__ef_bfloat16, true, true>(tops::__ef_bfloat16*, tops::__ef_bfloat16*, tops::__ef_bfloat16*, tops::__ef_bfloat16*, float*, int*, int*, int*, int, int, int, int, int, int, int, int)  |      | 19.863746ms  | 3.03%   | 0.413828ms | 0.413828 | 48   |     | 0.00877   | 0.0134923076923077  | 19.2161132307692 |         |
| void invoke_fused_moe_kernel_m_cut_intra_die<(MultiCoreCutType)2, tops::__ef_bfloat16, false, true>(tops::__ef_bfloat16*, tops::__ef_bfloat16*, tops::__ef_bfloat16*, tops::__ef_bfloat16*, float*, int*, int*, int*, int, int, int, int, int, int, int, int) |      | 17.243207ms  | 2.63%   | 0.359233ms | 0.359233 | 48   |     | 0.00877   | 0.0134923076923077  | 16.5955532307692 |         |
| fused_gdn_gating_kernel                                                                                                                                                                                                                                       |      | 16.559990ms  | 2.53%   | 0.459999ms | 0.459999 | 36   |     | 0.001     | 0.00153846153846154 | 16.5045793846154 |         |
| void binary_tensor_kernel<cc_kernel::MUL, unsigned char, true, false, false>(cc_kernel::MUL, unsigned char*, unsigned char*, unsigned char*, BINARY_OP_PARAS)                                                                                                 |      | 13.828569ms  | 2.11%   | 0.049743ms | 0.049743 | 278  |     |           |                     |                  |         |




主要几个算子差距

- *causal*conv1d_fwd_kernel ，占比14.79%
  - our： 2.688773ms 
  - gpu：0.004588
- solve_tril_16x16_kernel，占比3.13%
  - our： 0.568179ms
  - gpu：0.006423ms
- void invoke_fused_moe_kernel_m_cut_intra_die<(MultiCoreCutType)2, tops::__ef_bfloat16, true, true>(tops::__ef_bfloat16*, tops::__ef_bfloat16*, tops::__ef_bfloat16*, tops::__ef_bfloat16*, float*, int*, int*, int*, int, int, int, int, int, int, int, int) 占比3.03%
  - 

## decode




|                                                                                                                                                                                                                                                                                                                                                                                                                     |      |             |         |            |          |      |          |                     |                   |      |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---- | ----------- | ------- | ---------- | -------- | ---- | -------- | ------------------- | ----------------- | ---- |
| 名称                                                                                                                                                                                                                                                                                                                                                                                                                  | 开始时间 | 持续时间        | 百分比     | 平均时间       | op(ms)   | 数量   | gpu(ms)  | 65% gpu             | decode 提升         | opt  |
| 总计                                                                                                                                                                                                                                                                                                                                                                                                                  |      | 35.455515ms | 100.00% | 0.011437ms | 0.011437 | 3100 |          |                     |                   |      |
| ecclKernel_AllReduce_MESH_DIRECT_SIMPLE_Sum_bfloat(ecclWorkElem)                                                                                                                                                                                                                                                                                                                                                    |      | 5.494765ms  | 15.50%  | 0.056647ms | 0.056647 | 97   |          |                     |                   |      |
| void topk_softmax_kernel<float, true>(float*, float*, int*, int*, void*, TOPK_SOFTMAX_OP_PARAS, bool)                                                                                                                                                                                                                                                                                                               |      | 3.895236ms  | 10.99%  | 0.081150ms | 0.08115  | 48   | 0.003876 | 0.00596307692307692 | 3.60897230769231  | 0.04 |
| void matmul_kernel_lhs_all_in_l1_trans_split_n<tops::__ef_bfloat16, tops::__ef_bfloat16, tops::__ef_bfloat16, tops::__ef_bfloat16, tops::__ef_bfloat16, 1, false, true, false>(tops::__ef_bfloat16*, tops::__ef_bfloat16*, tops::__ef_bfloat16*, tops::__ef_bfloat16*, tops::__ef_bfloat16*, tops::__ef_bfloat16*, tops::__ef_bfloat16*, tops::__ef_bfloat16*, tops::__ef_bfloat16*, PRELU_OP_PARAS, GEMM_OP_PARAS) |      | 3.694193ms  | 10.42%  | 0.013336ms | 0.013336 | 277  |          | 0                   |                   |      |
| fused_recurrent_gated_delta_rule_fwd_kernel                                                                                                                                                                                                                                                                                                                                                                         |      | 2.976935ms  | 8.40%   | 0.082692ms | 0.082692 | 36   | 0.03104  | 0.0477538461538462  | 1.25777353846154  |      |
| void binary_tensor_kernel<cc_kernel::ADD, unsigned char, false, false, false>(cc_kernel::ADD, unsigned char*, unsigned char*, unsigned char*, BINARY_OP_PARAS)                                                                                                                                                                                                                                                      |      | 2.609150ms  | 7.36%   | 0.006011ms | 0.006011 | 434  |          |                     |                   |      |
| void binary_tensor_kernel<cc_kernel::MUL, unsigned char, true, false, false>(cc_kernel::MUL, unsigned char*, unsigned char*, unsigned char*, BINARY_OP_PARAS)                                                                                                                                                                                                                                                       |      | 1.507226ms  | 4.25%   | 0.008327ms | 0.008327 | 181  |          |                     |                   |      |
| void invoke_fused_moe_kernel_m_cut_intra_die<(MultiCoreCutType)2, tops::__ef_bfloat16, false, true>(tops::__ef_bfloat16*, tops::__ef_bfloat16*, tops::__ef_bfloat16*, tops::__ef_bfloat16*, float*, int*, int*, int*, int, int, int, int, int, int, int, int)                                                                                                                                                       |      | 1.353642ms  | 3.82%   | 0.028200ms | 0.0282   | 48   | 0.007    | 0.0107692307692308  | 0.836676923076923 |      |
| void to_kernel<float, tops::__ef_bfloat16>(float*, tops::__ef_bfloat16*, TO_OP_PARAS)                                                                                                                                                                                                                                                                                                                               |      | 1.226310ms  | 3.46%   | 0.004214ms | 0.004214 | 291  |          |                     |                   |      |
| void invoke_fused_moe_kernel_m_cut_intra_die<(MultiCoreCutType)2, tops::__ef_bfloat16, true, true>(tops::__ef_bfloat16*, tops::__ef_bfloat16*, tops::__ef_bfloat16*, tops::__ef_bfloat16*, float*, int*, int*, int*, int, int, int, int, int, int, int, int)                                                                                                                                                        |      | 1.137343ms  | 3.21%   | 0.023694ms | 0.023694 | 48   | 0.007    | 0.0107692307692308  | 0.620388923076923 |      |
| *causal*conv1d_update_kernel                                                                                                                                                                                                                                                                                                                                                                                        |      | 1.114095ms  | 3.14%   | 0.030947ms | 0.030947 | 36   | 0.001748 | 0.00268923076923077 | 1.01727969230769  |      |
| void binary_tensor_kernel<cc_kernel::MUL, unsigned char, false, false, false>(cc_kernel::MUL, unsigned char*, unsigned char*, unsigned char*, BINARY_OP_PARAS)                                                                                                                                                                                                                                                      |      | 1.056419ms  | 2.98%   | 0.006251ms | 0.006251 | 169  |          |                     |                   |      |
| void binary_tensor_kernel<cc_kernel::POW, unsigned char, false, false, false>(cc_kernel::POW, unsigned char*, unsigned char*, unsigned char*, BINARY_OP_PARAS)                                                                                                                                                                                                                                                      |      | 0.856603ms  | 2.42%   | 0.007079ms | 0.007079 | 121  |          |                     |                   |      |


# 算子分析



[https://qwen.ai/blog?id=4074cca80393150c248e508aa62983f9cb7d27cd&from=research.latest-advancements-list](https://qwen.ai/blog?id=4074cca80393150c248e508aa62983f9cb7d27cd&from=research.latest-advancements-list)

完整模型结构

我们分析Qwen3的整个模型调用栈，穿透到对应的目标算子：

```python
Qwen3NextForCausalLM.forward()
    └── Qwen3NextModel.forward()
        └── [Loop through layers]
            └── Qwen3NextDecoderLayer.forward() 
                ├── [if layer_type == "full_attention"]
                │   └── Qwen3NextAttention.forward()
                └── [if layer_type == "linear_attention"]
                    └── Qwen3NextGatedDeltaNet.forward()
                        └── torch.ops.vllm.gdn_attention() [Custom CUDA op]
                            ├── [Prefill mode]
                            │   └── chunk_gated_delta_rule()
                            └── [Decode mode] 
                                └── fused_recurrent_gated_delta_rule()
                                    
chunk_gated_delta_rule() [from vllm.model_executor.layers.fla.ops.chunk]
    ├── chunk_scaled_dot_kkt_fwd() 
    ├── solve_tril() 
    ├── recompute_w_u_fwd()
    ├── chunk_gated_delta_rule_fwd_h()
    └── chunk_fwd_o()

solve_tril() [from vllm.model_executor.layers.fla.ops.solve_tril]
    ├── solve_tril_16x16_kernel() [Base case: 16x16 blocks]
    └── [For larger matrices]
        ├── merge_16x16_to_32x32_inverse_kernel() [32x32]
        └── merge_16x16_to_64x64_inverse_kernel() [64x64]
```



## solve_tril 算子

Input arrives at Qwen3-Next attention layer
Queries (Q), Keys (K), Values (V) are computed

For chunk-based processing (64-token chunks typically):
Compute cumulative matrix A representing intra-chunk dependencies
Call solve_tril(A) to get (I+A)^-1
Use inverse to compute attention weights efficiently
Merge chunks using the hierarchical 16×16 → 32×32 → 64×64 approach

```python
def chunk_gated_delta_rule_fwd(q: torch.Tensor,
                               k: torch.Tensor,
                               v: torch.Tensor,
                               g: torch.Tensor,
                               beta: torch.Tensor,
                               scale: float,
                               initial_state: torch.Tensor,
                               output_final_state: bool,
                               cu_seqlens: Optional[torch.LongTensor] = None):
    g = chunk_local_cumsum(g, chunk_size=64, cu_seqlens=cu_seqlens)
    # obtain WY representation. u is actually the new v.
    A = chunk_scaled_dot_kkt_fwd(k=k,
                                 beta=beta,
                                 g_cumsum=g,
                                 cu_seqlens=cu_seqlens,
                                 output_dtype=torch.float32)
    A = solve_tril(A=A, cu_seqlens=cu_seqlens, output_dtype=k.dtype)
    w, u = recompute_w_u_fwd(
        k=k,
        v=v,
        beta=beta,
        A=A,
        g_cumsum=g,
        cu_seqlens=cu_seqlens,
    )
    h, v_new, final_state = chunk_gated_delta_rule_fwd_h(
        k=k,

```

在chunk_scaled_dot_kkt_fwd 中，Default chunk size: 64 (line 94)
tensor A=beta * K * K^T of shape `[B, T, H, BT]` where `BT` is the chunk size.

```python
def chunk_scaled_dot_kkt_fwd(
        k: torch.Tensor,
        beta: torch.Tensor,
        g_cumsum: Optional[torch.Tensor] = None,
        cu_seqlens: Optional[torch.LongTensor] = None,
        chunk_size: int = 64,
        output_dtype: torch.dtype = torch.float32) -> torch.Tensor:
    r"""
    Compute beta * K * K^T.

    Args:
        k (torch.Tensor):
            The key tensor of shape `[B, T, H, K]`.
        beta (torch.Tensor):
            The beta tensor of shape `[B, T, H]`.
        g_cumsum (torch.Tensor):
            The cumulative sum of the gate tensor of shape `[B, T, H]`.
            Default: None
        cu_seqlens (torch.LongTensor):
            The cumulative sequence lengths of the input tensor.
            Default: None
        chunk_size (int):
            The chunk size. Default: 64.
        output_dtype (torch.dtype):
            The dtype of the output tensor. Default: `torch.float32`

```

solve_tril 输入tensorA的A.shape[-1]=64

```python

def solve_tril(A: torch.Tensor,
               cu_seqlens: Optional[torch.Tensor] = None,
               output_dtype: torch.dtype = torch.float) -> torch.Tensor:
    """
    Compute the inverse of the lower triangular matrix
    A should be strictly lower triangular, i.e., A.triu() == 0.

    Args:
        A (torch.Tensor):
            [B, T, H, K]
        cu_seqlens (torch.Tensor):
            The cumulative sequence lengths of the input tensor.
            Default: None.
        output_dtype (torch.dtype):
            The dtype of the output tensor. Default: `torch.float`

    Returns:
        (I + A)^-1 with the same shape as A
```

TensorA shape 的维度信息：


| Dimension | Name                     | Meaning in Qwen3-Next Model                      | Determined By                                                  |
| --------- | ------------------------ | ------------------------------------------------ | -------------------------------------------------------------- |
| B         | Batch Size               | Number of sequences processed in parallel        | User's inference batch size / training batch                   |
| T         | Temporal/Sequence Length | Number of chunks (not tokens!) in the sequence   | num_chunks = T // chunk_size, where chunk_size is typically 64 |
| H         | Heads                    | Number of attention heads                        | Model config: num_attention_heads (e.g., 32, 64, etc.)         |
| K         | Chunk Size               | Size of each chunk block (must be 16, 32, or 64) | Fixed at 16, 32, or 64 for the triangular solve operation      |




进一步，我们分析solve_tril 的实现过程，尝试拆解下算法，是否能以较大的BT 粒度执行，总体上，整个执行流程可以拆解为：

Input Matrix Size   Processing Strategy

─────────────────────────────────────────

16×16            -> Direct: solve_tril_16x16_kernel only

32×32            -> Hierarchical: 16×16 base + merge_16x16_to_32x32

64×64            -> Hierarchical: 16×16 base + merge_16x16_to_64x64



其中solve_tril_16x16_kernel(A) 输入是一个16x16 的严格下三角矩阵，因此，求解（I+A）^-1 就变成，求解以下矩阵的逆：

- Case 1: BT = 16 (Input is 16×16)

Step 1: solve_tril_16x16_kernel computes (I + A_16x16)^-1 directly

Ad = solve_tril_16x16_kernel(A)  # Shape: [B, T, H, 16]

return Ad  # Done! No merging needed

只需要执行solve_tril_16x16_kernel(A)

- Case 2: BT = 32 (Input is 32×32)

Step 1: solve_tril_16x16_kernel processes all 16×16 diagonal blocks

Ad = solve_tril_16x16_kernel(A)  # Shape: [B, T, H, 16] 

# Ad contains: A11^-1, A22^-1 for each 32×32 matrix



# Step 2: erge_16x16_to_32x32_inverse_kernel builds 32×32 result

# Uses Ad results + original A to compute off-diagonal blocks

Ai = merge_16x16_to_32x32_inverse_kernel(A, Ad)  # Shape: [B, T, H, 32]

return Ai

- Case 3: BT = 64 (Input is 64×64)

# Step 1: solve_tril_16x16_kernel processes all 16×16 diagonal blocks  

Ad = solve_tril_16x16_kernel(A)  # Shape: [B, T, H, 16]

# Ad contains: A11^-1, A22^-1, A33^-1, A44^-1 for each 64×64 matrix



# Step 2: merge_16x16_to_64x64_inverse_kernel builds 64×64 result

# Complex hierarchical merging using the 16×16 diagonal results

Ai = merge_16x16_to_64x64_inverse_kernel(A, Ad)  # Shape: [B, T, H, 64]

return Ai



chunkBT=64

64×64 矩阵被分解为 4×4 个 16×16 子块，分两个level 实现计算，先是计算16x16 solve_tril_16x16_kernel, 再通过  merge_16x16_to_64x64_inverse_kernel 实现level 2. 详细过程如下：



- level 1

```
64×64 Matrix A:
     0   16   32   48   64
  ┌─────┬─────┬─────┬─────┐  0
  │ A11 │  0  │  0  │  0  │
  ├─────┼─────┼─────┼─────┤ 16  
  │ A21 │ A22 │  0  │  0  │
  ├─────┼─────┼─────┼─────┤ 32
  │ A31 │ A32 │ A33 │  0  │  
  ├─────┼─────┼─────┼─────┤ 48
  │ A41 │ A42 │ A43 │ A44 │
  └─────┴─────┴─────┴─────┘ 64

其中：
- A11, A22, A33, A44: 16×16 对角块 (需要求逆)
- A21, A31, A32, A41, A42, A43: 16×16 下三角块
- 上三角部分全为0


重新分组视图:
     0        32       64
  ┌─────────┬─────────┐  0
  │   B11   │    0    │
  │ (32×32) │         │ 
  ├─────────┼─────────┤ 32
  │   B21   │   B22   │
  │ (32×32) │ (32×32) │
  └─────────┴─────────┘ 64

其中:
B11 = ┌─────┬─────┐   B22 = ┌─────┬─────┐
      │ A11 │  0  │         │ A33 │  0  │ 
```

- level2

```python

# 完成Level 1后，我们有:
Level1_result = ┌─────────┬─────────┐
                │ B11^-1  │    0    │  
                ├─────────┼─────────┤
                │   ?     │ B22^-1  │  # B21^-1 待计算
                └─────────┴─────────┘
                
对于矩阵:  ┌─────────┬─────────┐
          │   B11   │    0    │
          ├─────────┼─────────┤
          │   B21   │   B22   │  
          └─────────┴─────────┘

逆矩阵:    ┌─────────┬─────────┐
          │ B11^-1  │    0    │
          ├─────────┼─────────┤  
          │ C21     │ B22^-1  │
          └─────────┴─────────┘

其中: C21 = -B22^-1 × B21 × B11^-1
C21 是32×32块，需要计算:
C21 = -B22^-1 @ B21 @ B11^-1

# B21的结构:
B21 = ┌─────┬─────┐  (A31  A32)
      │ A31 │ A32 │  (A41  A42)  
      ├─────┼─────┤
      │ A41 │ A42 │
      └─────┴─────┘
```





如果需要增加求解逆矩阵的最小单元粒度，这里比如从16x16 调整成32x32，需要修改的代码：

需要修改的文件

[solve_tril.py](https://solve_tril.py):

- 添加 solve_tril_32x32_kernel
- 添加 merge_32x32_to_64x64_inverse_kernel
- 修改 solve_tril 函数逻辑

[chunk_o.py](https://chunk_o.py):

- 更新默认 chunk_size 和最小值

[chunk_scaled_dot_kkt.py](https://chunk_scaled_dot_kkt.py):

- 更新默认 chunk_size

相关配置文件:

- 更新 BT_LIST 等配置参数

