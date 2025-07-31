# definitive_app.py
import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple
import pandas as pd
import numpy as np
# import matplotlib.pyplot as plt
# Try to import matplotlib for plotting; fallback if unavailable
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


def discover_patterns_h2o(dataframe):
    """
    Placeholder for H2O analysis. Implement pattern discovery with H2O here.
    """
    pass

def query_gpt4(prompt: str):
    """
    Placeholder for GPT -4.1 analysis. Implement API call to OpenAI here.
    """
    pass



@dataclass
class StrategyPerformance:
    fast_period: int
    slow_period: int
    total_return: float
    sharpe: float
    equity: pd.Series

def parse_data_file(file_path: Path) -> pd.DataFrame:
    ext = file_path.suffix.lower()
    if ext in ['.csv', '.txt']:
        df = pd.read_csv(file_path)
    else:
        raw = pd.read_excel(file_path, header=None)
        rows = [str(cell).split(',') for cell in raw[0]]
        header = [c.strip().strip('<>').strip() for c in rows[0]]
        data = rows[1:]
        df = pd.DataFrame(data, columns=header)
    df.columns = [c.strip().strip('<>').strip() for c in df.columns]
    if 'Date' in df.columns and 'Time' in df.columns:
        df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
        df = df.set_index('DateTime').drop(columns=['Date','Time'])
    elif 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date')
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col], errors='ignore')
        except Exception:
            pass
    if 'Close' not in df.columns:
        raise ValueError("Data must contain a 'Close' column")
    if not np.issubdtype(df['Close'].dtype, np.number):
        df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
    df = df.dropna(subset=['Close'])
    return df

def moving_average_crossover_signals(prices: pd.Series, fast: int, slow: int) -> pd.Series:
    fast_ma = prices.rolling(window=fast, min_periods=fast).mean()
    slow_ma = prices.rolling(window=slow, min_periods=slow).mean()
    signal = pd.Series(0, index=prices.index)
    prev_fast = fast_ma.shift(1)
    prev_slow = slow_ma.shift(1)
    cross_up = (fast_ma > slow_ma) & (prev_fast <= prev_slow)
    cross_down = (fast_ma < slow_ma) & (prev_fast >= prev_slow)
    signal[cross_up] = 1
    signal[cross_down] = 0
    signal = signal.ffill().fillna(0)
    return signal

def backtest_signals(prices: pd.Series, signal: pd.Series) -> pd.Series:
    returns = prices.pct_change().fillna(0)
    strategy_returns = returns * signal.shift(1).fillna(0)
    return (1 + strategy_returns).cumprod()

def compute_performance(equity: pd.Series) -> Tuple[float, float]:
    total_return = equity.iloc[-1] - 1
    equity_returns = equity.pct_change().dropna()
    sharpe = np.sqrt(252) * equity_returns.mean() / equity_returns.std() if equity_returns.std() != 0 else 0
    return total_return, sharpe

def find_best_edges(prices: pd.Series, fast_range: Tuple[int,int], slow_range: Tuple[int,int]) -> List[StrategyPerformance]:
    fast_start, fast_end = fast_range
    slow_start, slow_end = slow_range
    performances: List[StrategyPerformance] = []
    for fast in range(fast_start, fast_end + 1):
        for slow in range(max(fast + 1, slow_start), slow_end + 1):
            signal = moving_average_crossover_signals(prices, fast, slow)
            equity = backtest_signals(prices, signal)
            total_return, sharpe = compute_performance(equity)
            performances.append(StrategyPerformance(fast, slow, total_return, sharpe, equity))
    performances.sort(key=lambda p: (p.sharpe, p.total_return), reverse=True)
    return performances[:10]

def analyse_powerlanguage_file(path: Path) -> str:
    content = path.read_text(encoding='utf-8', errors='ignore')
    lines = content.splitlines()
    inputs = []
    rules = []
    for line in lines:
        s = line.strip()
        if s.lower().startswith('inputs:'):
            parts = s[len('inputs:'):].split(',')
            for p in parts:
                p = p.strip().rstrip(';')
                if '=' in p:
                    name, value = [x.strip() for x in p.split('=',1)]
                    inputs.append((name, value))
        elif any(k in s.lower() for k in ['buy','sell','short','cover']):
            rules.append(s)
    report = []
    if inputs:
        report.append('Found input parameters:')
        for name,value in inputs:
            report.append(f'  - {name} (default {value})')
    if rules:
        report.append('Detected trading rules:')
        report.extend([f'  • {r}' for r in rules])
    if not report:
        report.append('No obvious inputs or trading rules were detected.')
    return '\n'.join(report)

def generate_powerlanguage_strategy(name: str, fast: int, slow: int) -> str:
    return f"""
// Strategy: {name}
Inputs: FastLength({fast}), SlowLength({slow});
Vars: FastMA(0), SlowMA(0);
FastMA = XAverage(Close, FastLength);
SlowMA = XAverage(Close, SlowLength);
If (FastMA crosses over SlowMA) Then
    Buy (\"LongEntry\") next bar at market;
If (FastMA crosses under SlowMA) Then
    Sell (\"LongExit\") next bar at market;
"""

def plot_equity_curves(perfs: List[StrategyPerformance], limit: int = 5) -> None:
    plt.figure(figsize=(10,6))
    for perf in perfs[:limit]:
        label = f'Fast {perf.fast_period} Slow {perf.slow_period}'
        plt.plot(perf.equity.index, perf.equity.values, label=label)
    plt.legend()
    plt.title('Equity Curves')
    plt.xlabel('Date')
    plt.ylabel('Equity')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('top_equity_curves.png')

def main():
    parser = argparse.ArgumentParser(description='Analyse data and generate strategies.')
    parser.add_argument('--file', type=Path, required=True)
    parser.add_argument('--fast-range', nargs=2, type=int, default=[5,20])
    parser.add_argument('--slow-range', nargs=2, type=int, default=[30,60])
    parser.add_argument('--strategy-name', type=str, default='DefinitiveStrategy')
    parser.add_argument('--powerlanguage', type=Path)
    parser.add_argument('--output', type=Path, default=Path('definitive_strategy.txt'))
    args = parser.parse_args()
    df = parse_data_file(args.file)
    prices = df['Close']
    perfs = find_best_edges(prices, (args.fast_range[0], args.fast_range[1]), (args.slow_range[0], args.slow_range[1]))
    print('Top strategies:')
    for i, perf in enumerate(perfs[:5], start=1):
        print(f"{i}. Fast {perf.fast_period} Slow {perf.slow_period} -> Return: {perf.total_return:.2%}, Sharpe: {perf.sharpe:.2f}")
    if args.powerlanguage and args.powerlanguage.exists():
        print('\nAnalysis of existing PowerLanguage file:')
        print(analyse_powerlanguage_file(args.powerlanguage))
    best = perfs[0]
    code = generate_powerlanguage_strategy(args.strategy_name, best.fast_period, best.slow_period)
    args.output.write_text(code, encoding='utf-8')
    print(f'\nGenerated strategy saved to {args.output.resolve()}')
    plot_equity_curves(perfs)

if __name__ == '__main__':
    main()
