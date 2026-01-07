import pytest
from src.utils.parameter_optimizer import ParameterOptimizer

def test_parameter_bias():
    optimizer = ParameterOptimizer(base_config={})
    
    # Base case
    params_base = optimizer.optimize_parameters(performance_data={}, market_vix=20)
    
    # Case with "early profit" reflection
    lessons = [{"lesson_learned": "利確が早すぎたので、もっと利益を伸ばすべきだった。"}]
    params_biased = optimizer.optimize_parameters(performance_data={}, market_vix=20, recent_lessons=lessons)
    
    # TP should be higher in biased case
    assert params_biased["take_profit_pct"] > params_base["take_profit_pct"]
    print(f"Base TP: {params_base['take_profit_pct']}, Biased TP: {params_biased['take_profit_pct']}")

def test_stop_loss_bias():
    optimizer = ParameterOptimizer(base_config={})
    
    # Case with "tighten stop" reflection
    lessons = [{"lesson_learned": "損切りを早くすべきだった。"}]
    params_biased = optimizer.optimize_parameters(performance_data={}, market_vix=20, recent_lessons=lessons)
    
    # SL should be smaller (tighter) in biased case
    # Base SL is 0.05. 0.8x bias -> 0.04
    assert params_biased["stop_loss_pct"] < 0.05
    print(f"Biased SL: {params_biased['stop_loss_pct']}")

if __name__ == "__main__":
    test_parameter_bias()
    test_stop_loss_bias()
    print("AI Reflection Feedback tests passed!")
