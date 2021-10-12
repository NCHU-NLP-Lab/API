import threading
import time

import stanza
import torch
from loguru import logger
from transformers import (
    AutoModelForCausalLM,
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    BartForConditionalGeneration,
    BartTokenizerFast,
    BertTokenizerFast,
    RobertaForMultipleChoice,
    RobertaTokenizer,
)

QUESTION_GENERATION_ENG_MODEL = "p208p2002/bart-squad-qg-hl"
QUESTION_GENERATION_CHT_MODEL = "p208p2002/gpt2-drcd-qg-hl"
QUESTION_GROUP_GENERATION_MODEL = "p208p2002/qmst-qgg"
DISTRACTOR_GENERATION_ENG_MODEL = "voidful/bart-distractor-generation"
DISTRACTOR_GENERATION_SELECTION_RL_MODEL = "LIAMF-USP/roberta-large-finetuned-race"


class LanguageModels:
    def __init__(self, download_only=False):
        self.download_only = download_only
        if download_only:
            logger.info("Pre-Downloading Language Models")

        threads = [
            threading.Thread(target=self.init_eng_qg_model),
            threading.Thread(target=self.init_cht_qg_model),
            threading.Thread(target=self.init_eng_qgg_model),
            threading.Thread(target=self.init_eng_dg_model),
            threading.Thread(target=stanza.download, args=("en",)),
        ]

        start_at = time.time()

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        logger.info(f"Model loading took {(time.time() - start_at):.2f} secs")

    def init_eng_qg_model(self):
        logger.info("Start loading Enlish QG Model...")
        self.en_qg_model = AutoModelForSeq2SeqLM.from_pretrained(
            QUESTION_GENERATION_ENG_MODEL
        )
        self.en_qg_tokenizer = AutoTokenizer.from_pretrained(
            QUESTION_GENERATION_ENG_MODEL
        )
        logger.info("English QG Model loaded!")

    def init_cht_qg_model(self):
        logger.info("Start loading Chinese QG Model...")
        self.zh_qg_model = AutoModelForCausalLM.from_pretrained(
            QUESTION_GENERATION_CHT_MODEL
        )
        self.zh_qg_tokenizer = BertTokenizerFast.from_pretrained(
            QUESTION_GENERATION_CHT_MODEL
        )
        logger.info("Chinese QG Model loaded!")

    def init_eng_qgg_model(self):
        logger.info("Start loading Enlish QGG Model...")
        self.en_qgg_model = BartForConditionalGeneration.from_pretrained(
            QUESTION_GROUP_GENERATION_MODEL
        )
        self.en_qgg_model.to(
            torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
        )
        self.en_qgg_tokenizer = BartTokenizerFast.from_pretrained(
            QUESTION_GROUP_GENERATION_MODEL
        )
        logger.info("English QGG Model loaded!")

    def init_eng_dg_model(self):
        logger.info("Start loading Enlish DG Model...")
        dg_models = [
            AutoModelForSeq2SeqLM.from_pretrained(DISTRACTOR_GENERATION_ENG_MODEL),
            AutoModelForSeq2SeqLM.from_pretrained(
                f"{DISTRACTOR_GENERATION_ENG_MODEL}-pm"
            ),
            AutoModelForSeq2SeqLM.from_pretrained(
                f"{DISTRACTOR_GENERATION_ENG_MODEL}-both"
            ),
        ]
        dg_tokenizers = [
            AutoTokenizer.from_pretrained(DISTRACTOR_GENERATION_ENG_MODEL),
            AutoTokenizer.from_pretrained(f"{DISTRACTOR_GENERATION_ENG_MODEL}-pm"),
            AutoTokenizer.from_pretrained(f"{DISTRACTOR_GENERATION_ENG_MODEL}-both"),
        ]
        rl_model = RobertaForMultipleChoice.from_pretrained(
            DISTRACTOR_GENERATION_SELECTION_RL_MODEL
        )
        rl_tokenizer = RobertaTokenizer.from_pretrained(
            DISTRACTOR_GENERATION_SELECTION_RL_MODEL
        )

        if not self.download_only:
            from distractor_generation import BartDistractorGeneration

            self.en_dis_model = BartDistractorGeneration(
                dg_models, dg_tokenizers, rl_model, rl_tokenizer
            )
        logger.info("English DG Model loaded!")


if __name__ == "__main__":
    models = LanguageModels(download_only=True)
