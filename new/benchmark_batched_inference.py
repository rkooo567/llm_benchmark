from prompt_generator import PromptsGenerator
import argparse

LLAMA_MAX_SEQUENCE_LENGTH = 4096


def parse_args():
    parser = argparse.ArgumentParser(description="Benchmark inference")
    parser.add_argument("-k",
                        "--max_new_tokens",
                        type=int,
                        default=1024)
    parser.add_argument("-n",
                        "--num_queries",
                        type=int,
                        help="number of queries to run",
                        default=10)
    parser.add_argument("-w",
                        "--warmup",
                        type=int,
                        help="number of queries for warming up",
                        default=32)
    parser.add_argument("-l",
                        "--prompt_length",
                        help="average number of tokens each prompt.",
                        type=int,
                        default=1024)
    parser.add_argument('--framework', required=True, choices=['vllm', 'deepspeed', 'trtllm'])
    parser.add_argument("-tp",
                        "--tensor_para",
                        type=int,
                        help="Tensor parallelism",
                        default=1)
    parser.add_argument('--model', required=True, help="path to the model")

    args = parser.parse_args()
    return args


def benchmark_vllm(model, tp, num_queries, warmup, prompt_length, max_new_tokens):
    from vllm import LLM, SamplingParams

    # Create an LLM.
    llm = LLM(model=model, tensor_parallel_size=tp)
    
    # Create a sampling params object.
    sampling_params = SamplingParams(temperature=0, max_tokens=max_new_tokens)

    prompt_generator = PromptsGenerator(tokenizer_path=model)
    if warmup > 0:
        print('warmming up...')
        warmup_prompts = prompt_generator.generate(1024, 1024*0.3, 2048, warmup, show_progress=True)
        llm.generate(warmup_prompts, sampling_params)
        print('warm up finished')

    prompts = prompt_generator.generate(prompt_length, prompt_length*0.3, LLAMA_MAX_SEQUENCE_LENGTH-max_new_tokens, num_queries, show_progress=True)
    outputs = llm.generate(prompts, sampling_params)
    for output in outputs:
        print(output)


if __name__ == "__main__":
    args = parse_args()
    print('\n=============== Argument ===============')
    for key in vars(args):
        print('{}: {}'.format(key, vars(args)[key]))
    print('========================================')

    if args.framework == 'vllm':
        benchmark_vllm(
            model=args.model,
            tp=args.tensor_para,
            num_queries=args.num_queries,
            warmup=args.warmup,
            prompt_length=args.prompt_length,
            max_new_tokens=args.max_new_tokens)


# # Sample prompts.
# model_path = "/models/llama-2-7b-chat-hf/"
# prompt_generator = PromptsGenerator(tokenizer_path=model_path)

# prompts = prompt_generator.generate(1024, 1024*0.3, 4096-1024, 32, show_progress=True)


# # Generate texts from the prompts. The output is a list of RequestOutput objects
# # that contain the prompt, generated text, and other information.
# outputs = llm.generate(prompts, sampling_params)
# # Print the outputs.
# for output in outputs:
#     prompt = output.prompt
#     generated_text = output.outputs[0].text
#     print(f"Prompt: {prompt!r}, Generated text: {generated_text!r}")
