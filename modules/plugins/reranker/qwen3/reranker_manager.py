# from transformers import AutoTokenizer
# from vllm.engine.arg_utils import AsyncEngineArgs
# from vllm.engine.async_llm_engine import AsyncLLMEngine
# from vllm.sampling_params import SamplingParams
# from vllm.utils import random_uuid

# import os, math
# os.environ["TORCH_COMPILE_DISABLE"] = "1"
# os.environ["CUDA_VISIBLE_DEVICES"] = "0"  # 明确指定使用第0卡

# def format_instruction(instruction, query, doc):
#         return [
#             {"role": "system", "content": "Judge whether the Document meets the requirements based on the Query and the Instruct provided. Note that the answer can only be \"yes\" or \"no\"."},
#             {"role": "user", "content": f"<Instruct>: {instruction}\n\n<Query>: {query}\n\n<Document>: {doc}"}
#         ]

# class RerankerManager():
#     def __init__(self):
        
#         # 配置参数
#         MODEL_NAME = "/home/maosy6/Qwen3-Reranker-0.6B"
#         self.MAX_LENGTH = 8192
#         self.SUFFIX = "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
        
#         # 初始化组件
#         self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
#         self.tokenizer.padding_side = "left"
#         self.tokenizer.pad_token = self.tokenizer.eos_token
#         suffix_tokens = self.tokenizer.encode(self.SUFFIX, add_special_tokens=False)
#         self.true_token = self.tokenizer("yes", add_special_tokens=False).input_ids[0]
#         self.false_token = self.tokenizer("no", add_special_tokens=False).input_ids[0]
        
#         # 初始化vLLM引擎，只使用第0卡，优化显存使用
#         engine_args = AsyncEngineArgs(
#             model=MODEL_NAME,
#             tensor_parallel_size=1,
#             max_model_len=2048,  # 减少最大序列长度
#             gpu_memory_utilization=0.3,  # 大幅减少显存使用比例
#             enable_prefix_caching=False,  # 禁用前缀缓存节省显存
#             max_num_batched_tokens=2048,  # 限制批处理token数
#             max_num_seqs=16,  # 限制并发序列数
#         )
        
#         self.engine = AsyncLLMEngine.from_engine_args(engine_args)


#     def process_inputs(self, text_1, text_2, instruction):
#         prompts = []
#         for text1, text2 in zip(text_1, text_2):
#             messages = format_instruction(instruction, text1, text2)
#             prompt = self.tokenizer.apply_chat_template(
#                 messages, tokenize=False, add_generation_prompt=False
#             )
#             prompt = prompt[:self.MAX_LENGTH] + self.SUFFIX
#             prompts.append(prompt)
#         return prompts

#     async def rerank(self, text_1, text_2, instruction):
        
#         # 处理输入
#         prompts = self.process_inputs(text_1, text_2, instruction)        
        
#         # 创建采样参数
#         sampling_params = SamplingParams(
#             temperature=0,
#             max_tokens=1,
#             logprobs=20,
#             allowed_token_ids=[self.true_token, self.false_token]
#         )
        
#         # 创建请求并获取结果
#         outputs = []
#         request_ids = []
#         for prompt in prompts:
#             request_id = random_uuid()
#             request_ids.append(request_id)
#             outputs.append(
#                 self.engine.generate(
#                     prompt=prompt,
#                     sampling_params=sampling_params,
#                     request_id=request_id,
#                 )
#             )
        
#         # 等待所有请求完成
#         raw_results = []
#         for output in outputs:
#             async for result in output:
#                 raw_results.append(result)
#                 break  # 只取第一个结果
#         print(f"🧠reranker raw results: {len(raw_results)} items")
        
#         # 解析结果并格式化输出
#         processed_results = []
#         for i, result in enumerate(raw_results):
#             # 提取token和logprob信息
#             output_text = result.outputs[0].text  # "yes" 或 "no"
#             logprobs = result.outputs[0].logprobs[0] if result.outputs[0].logprobs else {}
            
#             # 获取yes和no的概率
#             yes_logprob = logprobs.get(self.true_token, None)
#             no_logprob = logprobs.get(self.false_token, None)
            
#             true_score = math.exp(yes_logprob.logprob) if yes_logprob else 0
#             false_score = math.exp(no_logprob.logprob) if no_logprob else 0
#             score = true_score / (true_score + false_score) if (true_score + false_score) > 0 else 0.5
            
#             processed_results.append({
#                 "index": i,
#                 "query": text_1[i] if i < len(text_1) else text_1[0] if text_1 else "",
#                 "document": text_2[i] if i < len(text_2) else text_2[0] if text_2 else "",
#                 "relevant": output_text == "yes",
#                 #"confidence": {
#                 #    "answer": output_text,
#                     # "yes_logprob": yes_logprob.logprob if yes_logprob else None,
#                     # "no_logprob": no_logprob.logprob if no_logprob else None，
                    
#                 #}
#                 "score": score
#             })
        
#         return {
#             "model": "Qwen3-Reranker-0.6B",
#             "results": processed_results,
#             "total_pairs": len(processed_results)
#         }