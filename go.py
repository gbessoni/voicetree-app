import openai
import os
import time

# Set up the OpenAI API key
openai.api_key = "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"


def extract_words_from_files(directory):
    words = []
    for filename in os.listdir(directory):
        if filename.startswith("w0rds") and filename.endswith(".txt"):
            try:
                with open(os.path.join(directory, filename), "r", encoding="utf-8") as file:
                    for line in file:
                        line = line.strip()
                        if "," in line:
                            # Take the content after the comma
                            word = line.split(", ")[-1].strip()
                            
                            # Clean the word to remove potential punctuation marks and ensure it's a single word
                            cleaned_word = word.strip('.,!?()[]{}":;')
                            if " " not in cleaned_word:  # Ensure it's a single word
                                words.append(cleaned_word)
            except Exception as e:
                print(f"Error reading {filename}: {e}")
    return words


def get_api_response(compare_phrase, words_batch):
    # Constructing the initial part of the prompt
    prompt = ('You are a semantic scoring algo. For each word I provide, tell me its semantic similarity to the compare phrase "' 
              + compare_phrase + 
              '" on a scale of -100% (not related at all even a contrary or as different as possible meaning) to 100% (perfectly semantically related, completely synonymous with the meaning of the compare phrase). Anything under 0 (from -1 to -100%) means not semantically related to the compare phrase at all. Please just give me the words: score back In a list, no other meta talk ')
    
    # Adding the Compare Phrase and the list of words to the prompt
    prompt += '\n\nCompare Phrase: ' + compare_phrase + '\n\nWords to compare and get a semantic relationship score to the idea of the compare phrase:'
    for word in words_batch:
        prompt += "\n- " + word

    # Making the API call
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    # Returning the API response and the constructed prompt
    return response["choices"][0]["message"]["content"], prompt


def score_and_sort_words(compare_phrase, words):
    batch_size = 300
    word_scores = {}
    failed_batches = []
    total_words = len(words)
    api_calls = 0
    total_cost = 0
    start_time = time.time()
    retries = 0
    i = 0
    while i < total_words:
        words_batch = words[i:i+batch_size]
        response_content, prompt = get_api_response(compare_phrase, words_batch)
        # Check if the response is in the expected format
        if all(": " in line for line in response_content.split('\n') if line):
            for line in response_content.split('\n'):
                if line and ": " in line:
                    word, score = line.split(": ")
                    word_scores[word] = score
            api_calls += 1
            elapsed_time = time.time() - start_time
            estimated_cost = api_calls * 0.003  # assuming a cost of $0.003 per API call
            print(f"Processed {min(i + batch_size, total_words)} out of {total_words} words. "
                  f"API calls made: {api_calls}. Estimated cost: ${estimated_cost:.2f}. "
                  f"Elapsed time: {elapsed_time:.2f} seconds.")
            retries = 0
            i += batch_size
        else:
            # If the response is not in the expected format, retry the API call
            if retries < 5:
                print("Unexpected response format. Retrying...")
                retries += 1
            else:
                print("Maximum retries reached. Skipping this batch.")
                failed_batches.append((words_batch, prompt))
                retries = 0
                i += batch_size

    # Ensure all scores are convertible to float, otherwise assign a default score of -100%
    def safe_float_conversion(score):
        try:
            return float(score.replace("%", ""))
        except ValueError:
            return -100.0

    sorted_word_scores = sorted(word_scores.items(), key=lambda x: safe_float_conversion(x[1]), reverse=True)
    
    # Save to a file
    with open("sorted_words_scores.txt", "w", encoding='utf-8') as file:
        for word, score in sorted_word_scores:
            file.write(f"{word}: {score}\n")
    print("Results saved to sorted_words_scores.txt")

    # Save failed batches to a separate log file
    if failed_batches:
        with open("failed_batches.log", "w", encoding='utf-8') as file:
            for batch, prompt in failed_batches:
                file.write("Words: " + ", ".join(batch) + "\n")
                file.write("Prompt: " + prompt + "\n\n")
        print("Failed batches saved to failed_batches.log")

    return sorted_word_scores

if __name__ == "__main__":
    compare_phrase = input("Please enter the compare phrase: ")
    words = extract_words_from_files(".")
    score_and_sort_words(compare_phrase, words)