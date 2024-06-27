import spacy
import streamlit
import json
import en_ner_bc5cdr_md
import en_ner_bionlp13cg_md
import en_ner_jnlpba_md


class FindingsExtractor:
    def __init__(self, st: streamlit):
        self.models = {
            #"en_core_sci_sm": en_core_sci_sm.load(),
            #"en_core_sci_md": en_core_sci_md.load(),
            "en_ner_bc5cdr_md": en_ner_bc5cdr_md.load(),
            "en_ner_bionlp13cg_md": en_ner_bionlp13cg_md.load(),
            "en_ner_jnlpba_md": en_ner_jnlpba_md.load(),
            #"en_ner_craft_md": en_ner_craft_md.load(),
            #"en_core_sci_scibert" : en_core_sci_scibert.load(),
            #"en_core_sci_lg": en_core_sci_lg.load()
        }
        self.st = st
        self.st.title("Findings from Radiology Reports")
        self.st.markdown("Input a radiology report to extract medical entities in a structured form.", unsafe_allow_html=True)
        self.report_text = self.st.text_area("Radiology Report", height=300)
        self.selected_models = []
        for model in self.models:
            if self.st.checkbox(model):
                self.selected_models.append(model)
        self.extract_button = self.st.button("Extract Findings")

    def extract_entities(self, report):
        entities = []
        for model_name in self.selected_models:
            nlp = self.models[model_name]
            doc = nlp(report)
            for ent in doc.ents:
                entities.append({
                    "original_term": ent.text,
                    "mapped_term": ent.label_,
                    "model": model_name  # Add the model name to the output
                })
        return entities

    def convert_to_json(self, entities):
        return json.dumps(entities, indent=4)

    def run(self):
        if self.extract_button:
            if self.report_text:
                entities = self.extract_entities(self.report_text)
                result_json = self.convert_to_json(entities)
                self.st.subheader("Extracted Entities")
                self.st.json(result_json)
            else:
                self.st.warning("Please input a radiology report.")

# Main function to run the Streamlit app
def main():
    extractor = FindingsExtractor()
    extractor.run()

if __name__ == "__main__":
    main()
