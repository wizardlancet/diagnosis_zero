import re
import random
from difflib import SequenceMatcher
from collections import Counter

# TODO: use a similarity
def extract_solution(solution_str, method='strict'):
    """
    Extract content wrapped by <answer></answer> from solution_str,
    with different behaviors based on the specified method.

    :param solution_str: A string containing <answer></answer> tags
    :param method: Extraction mode, either 'strict' or 'flexible'
    :return: The extracted answer or None if no valid answer is found
    """
    # Validate method parameter
    assert method in ['strict', 'flexible']

    final_answer = None

    if method == 'strict':
        # Strict mode: Extract the third <answer> content
        matches = re.findall(r'<answer>(.*?)</answer>', solution_str, re.DOTALL)
        if len(matches) >= 3:  # Check if there are at least 3 answers
            final_answer = matches[2].strip().lower()  # Get the third match (index 2)

    elif method == 'flexible':
        # Flexible mode: Extract all <answer> contents and return the last valid one
        matches = re.findall(r'<answer>(.*?)</answer>', solution_str, re.DOTALL)
        if matches:
            # Iterate through answers to find the last non-empty valid answer
            invalid_str = ['', '.']  # List of invalid answers
            for answer in reversed(matches):
                answer = answer.strip().lower()  # Remove leading/trailing spaces and convert to lowercase
                if answer not in invalid_str:
                    final_answer = answer
                    break

    return final_answer


def calculate_similarity(prediction, true_labels):
    """
    计算预测诊断与正确诊断的相似度
    
    Args:
        prediction: 预测的诊断结果（字符串）
        true_labels: 正确的诊断列表（字符串列表）
    
    Returns:
        float: 0-1之间的相似度分数
    """
    # 标准化处理
    prediction = prediction.lower().strip()
    true_labels = [label.lower().strip() for label in true_labels]
    
    # 完全匹配检查
    if prediction in true_labels:
        return 1.0
    
    # 计算与每个正确标签的相似度，取最大值
    max_similarity = 0.0
    
    for true_label in true_labels:
        # 1. 计算序列相似度 (0.3权重)
        sequence_sim = SequenceMatcher(None, prediction, true_label).ratio()
        
        # 2. 计算词集合相似度 (0.4权重)
        pred_words = set(re.findall(r'\w+', prediction))
        true_words = set(re.findall(r'\w+', true_label))
        
        if not pred_words or not true_words:
            word_sim = 0
        else:
            intersection = len(pred_words & true_words)
            union = len(pred_words | true_words)
            word_sim = intersection / union
        
        # 3. 计算词频相似度 (0.3权重)
        pred_word_freq = Counter(re.findall(r'\w+', prediction))
        true_word_freq = Counter(re.findall(r'\w+', true_label))
        
        all_words = set(pred_word_freq.keys()) | set(true_word_freq.keys())
        if not all_words:
            freq_sim = 0
        else:
            freq_diff_sum = sum(abs(pred_word_freq.get(word, 0) - true_word_freq.get(word, 0)) for word in all_words)
            max_freq_sum = sum(max(pred_word_freq.get(word, 0), true_word_freq.get(word, 0)) for word in all_words)
            freq_sim = 1 - (freq_diff_sum / (2 * max_freq_sum)) if max_freq_sum > 0 else 0
        
        # 综合评分
        similarity = 0.8 * sequence_sim + 0.1 * word_sim + 0.1 * freq_sim
        max_similarity = max(max_similarity, similarity)
    
    return max_similarity
    
    


def compute_score(solution_str, ground_truth, method='strict', format_score=0.1, score=1.):
    """The scoring function for countdown task.
    
    Args:
        solution_str: the solution text
        ground_truth: dictionary containing target number and available numbers
        method: the method to extract the solution
        format_score: the score for correct format but wrong answer
        score: the score for the correct answer
    """
    diagnosis_list = ground_truth['diagnosis']
    diagnosis_list_lower = [diagnosis.lower() for diagnosis in diagnosis_list]
        
    extracted_answer = extract_solution(solution_str=solution_str, method=method)
    
    do_print = random.randint(1, 64) == 1
    
    if do_print:
        print(f"--------------------------------")
        print(f"Target: {diagnosis_list}")
        print(f"Model Diagnosis: {extracted_answer}")
        print(f"Solution string: {solution_str}")

    if extracted_answer is None:
        if do_print:
            print(f"No equation found")
        return 0
    
    # Compare extracted answer with ground truth
    
    extracted_answer = extracted_answer.lower()
    
    # Calculate similarity score
    max_similarity = calculate_similarity(extracted_answer, diagnosis_list_lower)
    
    # If similarity is very high (>0.9), give full score
    if max_similarity > 0.8:
        return score
    
    return format_score

    #     # If similarity is very low (<0.2), give 0
    # if max_similarity < 0.2:
    #     return format_score
    
    # # Otherwise, give partial score based on similarity
    # # Scale the similarity score between format_score and score
    # partial_score = format_score + (score - format_score) * max_similarity
    
    # if do_print:
    #     print(f"Similarity score: {max_similarity}")
    #     print(f"Final score: {partial_score}")
    
    # return partial_score
    
    
    
    
