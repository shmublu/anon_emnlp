import transformers
import torch
import gc



class LlamaPipeline:
    def __init__(self, model_id='meta-llama/Meta-Llama-3-8B-Instruct'):
        self.pipeline = self.load_model(model_id)

    def load_model(self,model_id='meta-llama/Meta-Llama-3-8B-Instruct'):
        gc.collect()
        torch.cuda.empty_cache()
        gc.collect()
        pipeline = transformers.pipeline(
            "text-generation",
            model=model_id,
            model_kwargs={"torch_dtype": torch.bfloat16},
            device="cuda",
        )
        return pipeline


    def generate_response(self, messages, max_tokens=1400, temperature = 0.1):
        prompt = self.pipeline.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        terminators = [
            self.pipeline.tokenizer.eos_token_id,
            self.pipeline.tokenizer.convert_tokens_to_ids("<|eot_id|>")
        ]
        outputs = None
        if temperature:
            outputs = self.pipeline(
                prompt,
                max_new_tokens = max_tokens,
                eos_token_id = terminators,
                do_sample = True,
                temperature = temperature,
            )
        else:
            outputs = self.pipeline(
                prompt,
                max_new_tokens = max_tokens,
                eos_token_id = terminators,
                do_sample = False,
            )

        return outputs[0]["generated_text"][len(prompt):]

    def format_messages(self, role, list_of_messages):
        messages = []
        if role:
            messages.append({
                "role":"system",
                "content":role
            },)
        for index,msg in enumerate(list_of_messages):
            if index % 2 == 0:
                messages.append({
                    "role":"user",
                    "content":msg
                },)
            else:
                messages.append({
                    "role":"assistant",
                    "content":msg
                },)
        return messages





