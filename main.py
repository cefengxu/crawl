import requests
import concurrent.futures
import random
import string
import time
import json
from datetime import datetime

def generate_random_query(length=2):
    """生成随机查询字符串，使用中文常用词组减少被识别为机器人的风险"""
    queries = [
        "今天天气",
        "新闻热点",
        "美食推荐",
        "旅游攻略",
        "健康知识",
        "科技新闻",
        "电影推荐",
        "学习方法",
        "生活技巧",
        "音乐排行"
    ]
    return random.choice(queries)

def make_request(retry_count=3, retry_delay=2):
    """发送单个请求，带有重试机制"""
    url = "http://10.176.14.23:9407/api/v5/plgi/search"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    for attempt in range(retry_count):
        try:
            query = generate_random_query()
            data = {
                "query": query,
                "count": 10,
                "search_engine": "baidu"
            }
            
            start_time = time.time()
            response = requests.post(url, headers=headers, json=data)
            end_time = time.time()
            
            result = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "status_code": response.status_code,
                "response_time": end_time - start_time,
                "query": query,
                "attempt": attempt + 1
            }
            
            # 检查响应内容是否为空结果
            response_data = response.json()
            if not response_data.get("data"):
                result["error"] = "Empty search results"
                if attempt < retry_count - 1:
                    time.sleep(retry_delay * (attempt + 1))  # 指数退避
                    continue
            
            return result
            
        except Exception as e:
            if attempt < retry_count - 1:
                time.sleep(retry_delay * (attempt + 1))
            else:
                return {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status_code": -1,
                    "error": str(e),
                    "query": query,
                    "attempt": attempt + 1
                }

def run_parallel_test(concurrent_requests=5, total_iterations=10):
    """运行并行测试，降低并发数并加入间隔时间"""
    print(f"开始并行测试 - 并发数: {concurrent_requests}, 总迭代次数: {total_iterations}")
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
        for iteration in range(total_iterations):
            print(f"\n执行第 {iteration + 1} 次迭代")
            
            # 提交concurrent_requests个并发请求
            future_to_request = {executor.submit(make_request): i for i in range(concurrent_requests)}
            
            for future in concurrent.futures.as_completed(future_to_request):
                result = future.result()
                results.append(result)
                print(f"时间: {result['timestamp']}, "
                      f"查询: {result['query']}, "
                      f"状态码: {result['status_code']}, "
                      f"尝试次数: {result['attempt']}, "
                      f"响应时间: {result.get('response_time', 'N/A')}秒")
            
            # 每次迭代之间添加延时
            if iteration < total_iterations - 1:
                delay = random.uniform(1, 3)
                print(f"等待 {delay:.2f} 秒后进行下一次迭代...")
                time.sleep(delay)
    
    return results

if __name__ == "__main__":
    # 降低并发数，从20降到5
    results = run_parallel_test(concurrent_requests=5, total_iterations=10)
    
    # 计算统计信息
    successful_requests = [r for r in results if r["status_code"] == 200 and "error" not in r]
    avg_response_time = sum(r["response_time"] for r in successful_requests) / len(successful_requests) if successful_requests else 0
    
    print("\n测试统计:")
    print(f"总请求数: {len(results)}")
    print(f"成功请求数: {len(successful_requests)}")
    print(f"平均响应时间: {avg_response_time:.2f}秒")
    
    # 输出错误统计
    errors = [r for r in results if "error" in r]
    if errors:
        print("\n错误统计:")
        for error in errors:
            print(f"查询: {error['query']}, 错误: {error.get('error')}")
