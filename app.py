import streamlit as st
from multicharts_helper import ma_crossover_strategy, generate_powerlanguage_signal


def main():
    st.title("MultiCharts Strategy Generator")
    st.write("Genera codice PowerLanguage per una strategia di incrocio di medie mobili (EMA).")

    # Campi di input per nome e periodi
    name = st.text_input("Nome del segnale/strategia", "MyStrategy")
    fast_length = st.number_input(
        "Periodo della media mobile veloce",
        min_value=1,
        max_value=1000,
        value=14,
        step=1,
    )
    slow_length = st.number_input(
        "Periodo della media mobile lenta",
        min_value=1,
        max_value=1000,
        value=30,
        step=1,
    )

    # Bottone per generare il file
    if st.button("Genera file"):
        code_body = ma_crossover_strategy(name, fast_length, slow_length)
        # Genera il file .txt e legge il contenuto
        file_path = generate_powerlanguage_signal(name, code_body)
        with open(file_path, "r", encoding="utf-8") as f:
            file_contents = f.read()
        st.success(f"File generato: {file_path.name}")
        # Mostra anteprima del file
        st.text_area("Anteprima codice", file_contents, height=300)
        # Bottone per scaricare il file
        st.download_button(
            label="Scarica file .txt",
            data=file_contents,
            file_name=file_path.name,
            mime="text/plain",
        )


if __name__ == "__main__":
    main()
