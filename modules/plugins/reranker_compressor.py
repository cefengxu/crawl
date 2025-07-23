from langchain_text_splitters import RecursiveCharacterTextSplitter
# from anytree import Node
# from ..utils.utils import TokenCounterService
import asyncio
# from concurrent.futures import ThreadPoolExecutor

# class chunkNode(Node):
#     def __init__(self, name, content, score=0, token=0, id='0', parent=None, children=None, **kwargs):
#         super().__init__(name, parent=parent, children=children, **kwargs)
#         self.score = score
#         self.token = token
#         self.content = content
#         self.id = id

class RerankerCompressor():
    def __init__(self,config):
        separators = [
        "\n\n",
        "\n",
        "。",
        ".",
        "\uff0e",  # Fullwidth full stop
        "\u3002",  # Ideographic full stop
        ]
        refiner_config = config.get('refiner', {})
        self.initial_threshold = refiner_config.get('reranker_initial_threshold')
        self.step_threshold = refiner_config.get('reranker_step_threshold')
        self.splitter_list = refiner_config.get('reranker_split_level_list',[])
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.splitter_list[0],
            chunk_overlap=0,
            length_function=len,
            is_separator_regex=False,
            separators=separators
        )
        # self.executor = ThreadPoolExecutor()
        # self.token_counter = TokenCounterService(config)
        
    def get_split_text(self, text: str, chunk_size: int):
        # self.text_splitter._chunk_size = int(chunk_size*(len(text)/self.token_counter.get_tokens(text)))
        self.text_splitter._chunk_size = chunk_size 
        return self.text_splitter.split_text(text)       
       
    # def compress(self, query:str, contents:str, reranker, token_limit=0):
    #     result_node=[]
    #     total_token = 0
    #     max_value = 0
    #     contents = contents[0] if isinstance(contents, list)else contents
    #     if len(contents) > 2048:
    #         # root = chunkNode(f"Org_(1)", content=contents, score=1, token=self.token_counter.get_tokens(contents))
    #     else:
    #         try:
    #             root_score = reranker.rerank([query], [[contents]], [['1']], 1, threshold_after_norm=0)[0][0]['score']
    #             max_value = root_score
    #             if root_score < self.initial_threshold:
    #                 return "", 0
    #         except Exception as e:
    #             root_score = 1
    #         root = chunkNode(f"Org_({str(round(root_score,3))})", content = contents, score = root_score, token = self.token_counter.get_tokens(contents))
            
    #     content_list = [root]
    #     for chunk_size in self.splitter_list:
    #         if total_token + sum([node.token for node in content_list]) < token_limit:
    #             break
    #         content_list_for_single = content_list
    #         content_list = []
    #         for node in content_list_for_single:
    #             if node.token <= chunk_size:
    #                 content_list.append(node)
    #                 continue
    #             # Adpate the chunk size to the length of the content
    #             self.text_splitter._chunk_size = int(chunk_size*(len(node.content)/self.token_counter.get_tokens(node.content)))
    #             chunks = self.text_splitter.split_text(node.content)
    #             chunks_id = [str(i) for i in range(len(chunks))]

    #             rerank_result = reranker.rerank([query], [chunks], [chunks_id], len(chunks), threshold_after_norm = 0)
    #             keep_father_flag = True
    #             for chunk_result in rerank_result[0]:
    #                 score = chunk_result['score']
    #                 item = chunk_result['content']
    #                 chunk_id = chunk_result['chunkId']
    #                 if node.score - score < self.step_threshold or score > self.initial_threshold:
    #                     child = Node(name=f"{chunk_size}_{str(chunk_id)}_({str(round(score,3))})", content=item, score=score, token=self.token_counter.get_tokens(item), id=f"{node.id}-{str(chunk_id)}", parent=node)
    #                     content_list.append(child)
    #                     max_value = score if score > max_value else max_value
    #                     keep_father_flag = False
    #             if keep_father_flag:
    #                 result_node.append(node)
    #                 total_token += node.token
    #     result_node.extend(content_list)
        
        # if token_limit > 0:
        #     # sort by score
        #     result_node = sorted(result_node, key=lambda x: x.score, reverse=True)
        #     token_count = 0
        #     for i in range(len(result_node)):
        #         token_count += result_node[i].token
        #         if token_count > token_limit:
        #             result_node = result_node[:i]
        #             break
        # # sort by id
        # sorted_sequences = sorted(result_node, key=lambda x: (x.id))
        # text_result = ''.join([node.content for node in sorted_sequences])
        # return text_result, max_value
    
    # def faster_compress(self, query:str, contents:str, reranker, token_limit = 0):
    #     result_node=[]
    #     total_token = 0
    #     max_value = 0
    #     contents = contents[0] if isinstance(contents, list)else contents
    #     if len(contents) > 2048:
    #         root = chunkNode(f"Org_(1)", content=contents, score=1, token=self.token_counter.get_tokens(contents))
    #     else:
    #         try:
    #             root_score = reranker.rerank([query], [[contents]], [['1']], 1, threshold_after_norm=0)[0][0]['score']
    #             max_value = root_score
    #             if root_score < self.initial_threshold:
    #                 return "", 0
    #         except Exception as e:
    #             root_score = 1
    #         root = chunkNode(f"Org_({str(round(root_score,3))})", content = contents, score = root_score, token = self.token_counter.get_tokens(contents))
            
    #     content_list = [root]
    #     for chunk_size in self.splitter_list:
    #         if total_token + sum([node.token for node in content_list]) < token_limit:
    #             break
    #         content_list_for_single = content_list
    #         content_list = []
    #         batch_chunks = []
    #         batch_chunks_id = []
    #         batch_queries = []
    #         batch_nodes = []
    #         for node in content_list_for_single:
    #             if node.token <= chunk_size:
    #                 content_list.append(node)
    #                 continue
    #             # Adpate the chunk size to the length of the content
    #             self.text_splitter._chunk_size = int(chunk_size*(len(node.content)/self.token_counter.get_tokens(node.content)))
    #             chunks = self.text_splitter.split_text(node.content)
    #             chunks_id = [str(i) for i in range(len(chunks))]
    #             batch_chunks.append(chunks)
    #             batch_chunks_id.append(chunks_id)
    #             batch_queries.append(query)
    #             batch_nodes.append(node)
                
    #         if batch_chunks:
    #              # Get the length of the longest group in batch_chunks
    #             max_group_length = max(len(group) for group in batch_chunks)
    #             # rerank
    #             rerank_results = reranker.rerank(batch_queries, batch_chunks, batch_chunks_id, max_group_length, threshold_after_norm = 0)

    #             for idx, rerank_result in enumerate(rerank_results):
    #                 keep_father_flag = True
    #                 node = batch_nodes[idx]
    #                 for chunk_result in rerank_result:
    #                     score = chunk_result['score']
    #                     item = chunk_result['content']
    #                     chunk_id = chunk_result['chunkId']
    #                     if node.score - score < self.step_threshold or score > self.initial_threshold:
    #                         child = Node(name=f"{chunk_size}_{str(chunk_id)}_({str(round(score,3))})", content=item, score=score, token=self.token_counter.get_tokens(item), id=f"{node.id}-{str(chunk_id)}", parent=node)
    #                         content_list.append(child)
    #                         max_value = score if score > max_value else max_value
    #                         keep_father_flag = False
    #                 if keep_father_flag:
    #                     result_node.append(node)
    #                     total_token += node.token
                        
    #     result_node.extend(content_list)
        
    #     if token_limit > 0:
    #         # sort by score
    #         result_node = sorted(result_node, key=lambda x: x.score, reverse=True)
    #         token_count = 0
    #         for i in range(len(result_node)):
    #             token_count += result_node[i].token
    #             if token_count > token_limit:
    #                 result_node = result_node[:i]
    #                 break
    #     # sort by id
    #     sorted_sequences = sorted(result_node, key=lambda x: (x.id))
    #     text_result = ''.join([node.content for node in sorted_sequences])
    #     return text_result, max_value
    
    # async def async_compress(self, query, contents, reranker, token_limit=1024):
    #     loop = asyncio.get_running_loop()
    #     result = await loop.run_in_executor(self.executor, self.faster_compress, query, contents, reranker, token_limit)
    #     return result
    
    # async def async_compress(self, query, contents, reranker, token_limit=1024, initial_threshold=0.45, step_threshold=0.05, split_level_list: list = [1024, 512, 256]):
    #     result_node = []
    #     max_value = 0
    #     root_token = self.token_counter.get_tokens(contents)
    #     if root_token > 2048:
    #         root = chunkNode(f"Org_(1)", content=contents, score=1, token=root_token)
    #     else:
    #         try:
    #             root_score = (await reranker.async_rerank([query], [[contents]], [['1']], 1, threshold_after_norm=0))[0][0]['score']
    #             max_value = root_score
    #             if root_score < initial_threshold:
    #                 return "", 0
    #         except Exception as e:
    #             root_score = 1
    #         root = chunkNode(f"Org_({str(round(root_score, 3))})", content=contents, score=root_score, token=self.token_counter.get_tokens(contents))
    #     content_list = [root]
    #     for chunk_size in split_level_list:
    #         content_list_for_single = content_list
    #         content_list = []
    #         for node in content_list_for_single:
    #             if node.token <= chunk_size:
    #                 content_list.append(node)
    #                 continue
    #             # Adapt the chunk size to the length of the content
    #             self.text_splitter._chunk_size = int(chunk_size * (len(node.content) / self.token_counter.get_tokens(node.content)))
    #             chunks = self.text_splitter.split_text(node.content)
    #             chunks_id = [str(i) for i in range(len(chunks))]

    #             rerank_result = await reranker.async_rerank([query], [chunks], [chunks_id], len(chunks), threshold_after_norm=0)
    #             keep_father_flag = True
    #             for chunk_result in rerank_result[0]:
    #                 score = chunk_result['score']
    #                 item = chunk_result['content']
    #                 chunk_id = chunk_result['chunkId']
    #                 if node.score - score < step_threshold or score > initial_threshold:
    #                     child = Node(name=f"{chunk_size}_{str(chunk_id)}_({str(round(score, 3))})", content=item, score=score, token=self.token_counter.get_tokens(item), id=f"{node.id}-{str(chunk_id)}", parent=node)
    #                     content_list.append(child)
    #                     max_value = score if score > max_value else max_value
    #                     keep_father_flag = False
    #             if keep_father_flag:
    #                 result_node.append(node)
    #     result_node.extend(content_list)

    #     if token_limit > 0:
    #         # Sort by score
    #         result_node = sorted(result_node, key=lambda x: x.score, reverse=True)
    #         token_count = 0
    #         for i in range(len(result_node)):
    #             token_count += result_node[i].token
    #             if token_count > token_limit:
    #                 result_node = result_node[:i]
    #                 break
    #     # Sort by id
    #     sorted_sequences = sorted(result_node, key=lambda x: x.id)
    #     text_result = ''.join([node.content for node in sorted_sequences])
    #     return text_result, max_value    