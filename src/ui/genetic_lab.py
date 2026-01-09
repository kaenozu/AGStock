import streamlit as st
import pandas as pd
import time
from src.optimization.genetic_breeder import GeneticStrategyBreeder


def render_genetic_lab():
    st.markdown(
        """
        <div style="padding: 1rem; background: linear-gradient(90deg, #1a2a6c, #b21f1f, #fdbb2d); border-radius: 10px; color: white;">
            <h2>🧬 Genetic Strategy Lab</h2>
            <p>進化論的アプローチにより、数千世代の交配を経て最強の戦略パラメータを生成します。</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    if "genetic_breeder" not in st.session_state:
        st.session_state["genetic_breeder"] = GeneticStrategyBreeder(population_size=50)
        st.session_state["genetic_breeder"].initialize_population()

    breeder = st.session_state["genetic_breeder"]

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("🔬 Control Panel")
        generations_to_run = st.slider("Execute Generations", 1, 100, 10)
        mutation_rate = st.slider("Mutation Rate", 0.0, 0.5, 0.1)
        breeder.mutation_rate = mutation_rate

        if st.button("🧬 Start Evolution Cycle", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            best_fitness_history = []

            for i in range(generations_to_run):
                population = breeder.run_generation()
                best = population[0]
                best_fitness_history.append(best.fitness)

                status_text.text(
                    f"Processing Generation {breeder.generation_count}... Best Fitness: {best.fitness:.1f}"
                )
                progress_bar.progress((i + 1) / generations_to_run)
                time.sleep(0.05)  # UI update simulation

            st.success(f"Evolution Completed! {generations_to_run} generations evolved.")

            # Save history for chart
            st.session_state["evo_history"] = best_fitness_history

    with col2:
        st.subheader("📊 Evolution Status")
        if "evo_history" in st.session_state:
            st.line_chart(st.session_state["evo_history"])
            st.caption("Fitness Score Improvement over Generations")

        st.subheader("🏆 The Current Elite (Top 5)")

        # Display DataFrame of population
        data = []
        for dna in breeder.population[:10]:
            data.append(
                {
                    "Rank": breeder.population.index(dna) + 1,
                    "Name": dna.name,
                    "Fitness": f"{dna.fitness:.1f}",
                    "RSI Period": dna.rsi_period,
                    "SMA (S/L)": f"{dna.sma_short}/{dna.sma_long}",
                    "StopLoss": f"{dna.stop_loss_pct*100:.1f}%",
                    "TakeProfit": f"{dna.take_profit_pct*100:.1f}%",
                    "Generation": dna.generation,
                }
            )

        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)

        if st.button("💾 Deploy Best Genome to Production"):
            best = breeder.population[0]

            # Save to JSON
            import json
            import os

            # ディレクトリ作成（念のため）
            os.makedirs("models/config", exist_ok=True)

            params = {
                "name": best.name,
                "rsi_period": best.rsi_period,
                "rsi_lower": best.rsi_lower,
                "rsi_upper": best.rsi_upper,
                "sma_short": best.sma_short,
                "sma_long": best.sma_long,
                "stop_loss_pct": best.stop_loss_pct,
                "take_profit_pct": best.take_profit_pct,
                "fitness": best.fitness,
                "deployed_at": str(pd.Timestamp.now()),
            }

            with open("models/config/evolved_strategy_params.json", "w", encoding="utf-8") as f:
                json.dump(params, f, indent=4)

            st.toast(
                f"Strategy '{best.name}' (Fitness: {best.fitness:.1f}) has been deployed to the neural core!", icon="🚀"
            )
            st.balloons()
