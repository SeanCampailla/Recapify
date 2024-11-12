#test_project.py
import asyncio

import matplotlib.pyplot as plt
from bert_score import score
from rouge_score import rouge_scorer
from tabulate import tabulate
import openai
import spacy

import time
import tracemalloc

# Carica il modello di lingua italiana di spaCy
nlp = spacy.load("it_core_news_sm")

class SummaryEvaluator:
    def __init__(self, api_key):
        openai.api_key = api_key

    async def evaluate_rouge(self, generated_summary, original_text):
        scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
        scores = scorer.score(original_text, generated_summary)

        rouge_f1_scores = {
            "ROUGE-1": scores['rouge1'].fmeasure,
            "ROUGE-2": scores['rouge2'].fmeasure,
            "ROUGE-L": scores['rougeL'].fmeasure
        }
        return rouge_f1_scores

    async def evaluate_bert_score(self, generated_summary, original_text):
        _, _, F1 = score([generated_summary], [original_text], lang="it")
        return F1.mean().item()

    def extract_keywords(self, text):
        """Estrae le parole chiave principali (sostantivi, aggettivi, verbi) da un testo."""
        doc = nlp(text)
        keywords = [token.lemma_ for token in doc if token.pos_ in {"NOUN", "ADJ", "VERB"}]
        return keywords

    def jaccard_similarity(self, list1, list2):
        """Calcola la similarità di Jaccard tra due liste."""
        set1, set2 = set(list1), set(list2)
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union != 0 else 0

    async def evaluate_summary_keywords(self, generated_summary, original_text):
        """Valuta la similarità delle parole chiave tra riassunto e testo originale."""
        original_keywords = self.extract_keywords(original_text)
        summary_keywords = self.extract_keywords(generated_summary)
        return self.jaccard_similarity(original_keywords, summary_keywords)

    async def run_all_tests(self, generated_summary, original_text):
        # Crea le task per eseguire i vari test in parallelo
        rouge_task = self.evaluate_rouge(generated_summary, original_text)
        bert_task = self.evaluate_bert_score(generated_summary, original_text)
        keywords_task = self.evaluate_summary_keywords(generated_summary, original_text)

        # Esegui tutti i test e attendi i risultati
        rouge_results, bert_results, keywords_score = await asyncio.gather(
            rouge_task, bert_task, keywords_task
        )

        # Visualizza o salva i risultati
        self.display_results(rouge_results, bert_results, keywords_score)
        self.save_fidelity_report_tex(rouge_results, bert_results, keywords_score)

    def display_results(self, rouge_scores, bert_score, keywords_score):
        """Mostra i risultati F1 per ROUGE, BERT e la similarità delle parole chiave."""
        data = [
            ["ROUGE-1", rouge_scores["ROUGE-1"]],
            ["ROUGE-2", rouge_scores["ROUGE-2"]],
            ["ROUGE-L", rouge_scores["ROUGE-L"]],
            ["BERTScore", bert_score],
            ["Jaccard Keywords Similarity", keywords_score]
        ]

        print("\n--- Risultati per ROUGE, BERTScore e Similarità Parole Chiave ---\n")
        print(tabulate(data, headers=["Metric", "Score"], tablefmt="fancy_grid", floatfmt=".4f"))

    @staticmethod
    def save_fidelity_report_tex(rouge_scores, bert_score, keywords_score, filename="fidelity_report.tex"):
        """
        Salva i risultati del test di fedeltà in un formato tabella LaTeX.
        """
        with open(filename, "w") as file:
            file.write("\\begin{table}[h!]\n")
            file.write("\\centering\n")
            file.write("\\begin{tabular}{|l|r|}\n")
            file.write("\\hline\n")
            file.write("Metrica & Valore \\\\\n")
            file.write("\\hline\n")
            file.write(f"ROUGE-1 & {rouge_scores['ROUGE-1']:.4f} \\\\\n")
            file.write(f"ROUGE-2 & {rouge_scores['ROUGE-2']:.4f} \\\\\n")
            file.write(f"ROUGE-L & {rouge_scores['ROUGE-L']:.4f} \\\\\n")
            file.write(f"BERTScore & {bert_score:.4f} \\\\\n")
            file.write(f"Jaccard Keywords Similarity & {keywords_score:.4f} \\\\\n")
            file.write("\\hline\n")
            file.write("\\end{tabular}\n")
            file.write("\\caption{Risultati dei test di fedeltà con ROUGE, BERTScore e Similarità Parole Chiave}\n")
            file.write("\\label{tab:fidelity_results}\n")
            file.write("\\end{table}\n")

        print(f"Risultati dei test di fedeltà salvati in '{filename}'\n")

class PerformanceEvaluator:
    def __init__(self):
        self.results = {}
        self.parent_stack = []
        self.tracemalloc_started = False

    def start(self, func_name):
        if func_name not in self.results:
            self.results[func_name] = {
                "execution_time": 0,
                "current_memory_usage": 0,
                "peak_memory_usage": 0,
                "calls": 0
            }

        # Inizia il tracciamento della memoria se non è già stato avviato
        if not self.tracemalloc_started:
            tracemalloc.start()
            self.tracemalloc_started = True

        # Salva lo stato iniziale del tempo e della memoria
        self.results[func_name]["start_time"] = time.time()
        self.results[func_name]["start_memory"] = tracemalloc.take_snapshot()

        # Aggiunge la funzione alla pila per tracciare la gerarchia
        self.parent_stack.append(func_name)

    def stop(self, func_name):
        end_time = time.time()
        end_memory_snapshot = tracemalloc.take_snapshot()

        # Calcola l'utilizzo di memoria e tempo per questa chiamata specifica
        current_memory = sum([stat.size_diff for stat in end_memory_snapshot.compare_to(self.results[func_name]["start_memory"], 'lineno') if stat.size_diff > 0]) / (1024 * 1024)
        peak_memory = max(self.results[func_name]["peak_memory_usage"], current_memory)

        # Accumula i risultati
        self.results[func_name]["execution_time"] += end_time - self.results[func_name]["start_time"]
        self.results[func_name]["current_memory_usage"] += current_memory
        self.results[func_name]["peak_memory_usage"] = peak_memory
        self.results[func_name]["calls"] += 1

        # Rimuove la funzione dalla pila e accumula i risultati nel genitore, se esiste
        self.parent_stack.pop()
        if self.parent_stack:
            parent_func = self.parent_stack[-1]
            self.accumulate_results(parent_func, func_name)

    def accumulate_results(self, parent_func, child_func):
        # Accumula i risultati del child_func nel parent_func
        if parent_func in self.results and child_func in self.results:
            self.results[parent_func]["execution_time"] += self.results[child_func]["execution_time"]
            self.results[parent_func]["current_memory_usage"] += self.results[child_func]["current_memory_usage"]
            self.results[parent_func]["peak_memory_usage"] = max(
                self.results[parent_func]["peak_memory_usage"],
                self.results[child_func]["peak_memory_usage"]
            )

    def print_results(self):
        """Stampa i risultati esatti per ciascuna funzione, senza calcolo della media."""
        for func, report in self.results.items():
            print(f"Risultati esatti per {func}:")
            print(f"  Tempo di esecuzione totale: {report['execution_time']:.4f} s")
            print(f"  Memoria corrente totale: {report['current_memory_usage']:.4f} MB")
            print(f"  Picco di memoria totale: {report['peak_memory_usage']:.4f} MB")
            print(f"  Numero di chiamate: {report['calls']}")
        print("\n--- Fine dei Risultati di Performance ---\n")

eval = PerformanceEvaluator()