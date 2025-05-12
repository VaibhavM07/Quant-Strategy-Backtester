import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
from tqdm import tqdm

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

class PriceOption():
    def __init__(self, Spot, Strike, dtt, time_to_maturity, risk_free_rate, sigma, no_simulations,simulation_count,Z_matrix):
        self.Spot = Spot
        self.Strike = Strike
        self.time_to_maturity = time_to_maturity
        self.dt = self.time_to_maturity / dtt
        self.num = dtt
        self.risk_free_rate = risk_free_rate
        self.sigma = sigma
        self.no_simulations = no_simulations
        self.simulation_count=simulation_count
        self.discount = np.exp(-self.risk_free_rate * self.time_to_maturity)
        self.Z_matrix = Z_matrix

    def euler_asset_paths(self):
        simulations_euler = np.zeros(shape=(self.num, self.no_simulations))
        simulations_euler[0] = self.Spot
        dw_matrix = self.Z_matrix * np.sqrt(self.dt)
        for i in tqdm(range(1, self.num), desc=f"Simulating Euler paths of simulation {self.simulation_count}"):
            Z = np.random.normal(0, 1, self.no_simulations)
            dw = dw_matrix[i - 1]
            simulations_euler[i] = (
                        simulations_euler[i - 1] + simulations_euler[i - 1] * self.risk_free_rate * self.dt +
                        simulations_euler[i - 1] * self.sigma * dw)
        return simulations_euler

    def euler_discounted_payoff(self):
        asset_path = self.euler_asset_paths()
        european_call_payoff = np.maximum(asset_path - self.Strike, 0)
        european_option_discounted_value = np.mean(european_call_payoff[-1]) * self.discount
        binary_call_payoff = (asset_path > self.Strike).astype(float)
        binary_option_discounted_value = np.mean(binary_call_payoff[-1]) * self.discount
        return asset_path, european_call_payoff, binary_call_payoff, european_option_discounted_value, binary_option_discounted_value

    def milstein_asset_paths(self):
        simulations_milstein = np.zeros(shape=(self.num, self.no_simulations))
        simulations_milstein[0] = self.Spot
        dw_matrix = self.Z_matrix * np.sqrt(self.dt)
        for i in tqdm(range(1, self.num), desc=f"Simulating Milstein paths of simulation {self.simulation_count}"):
            dw = dw_matrix[i - 1]
            corrective_term = 0.5 * self.sigma ** 2 * simulations_milstein[i - 1] * ((dw ** 2) - self.dt)
            simulations_milstein[i] = simulations_milstein[i - 1] + simulations_milstein[
                i - 1] * self.risk_free_rate * self.dt + simulations_milstein[i - 1] * self.sigma * dw + corrective_term
        return simulations_milstein

    def milstein_discounted_payoff(self):
        asset_path = self.milstein_asset_paths()
        european_call_payoff = np.maximum(asset_path - self.Strike, 0)
        european_option_discounted_value = np.mean(european_call_payoff[-1]) * self.discount
        binary_call_payoff = (asset_path > self.Strike).astype(float)
        binary_option_discounted_value = np.mean(binary_call_payoff[-1]) * self.discount
        return asset_path, european_call_payoff, binary_call_payoff, european_option_discounted_value, binary_option_discounted_value

    def close_from_asset_paths(self):
        simulations = np.zeros(shape=(self.num, self.no_simulations))
        simulations[0] = self.Spot
        dw_matrix = self.Z_matrix * np.sqrt(self.dt)
        for i in tqdm(range(1, self.num), desc=f"Simulating Closed-form paths of simulation {self.simulation_count}"):
            Z = np.random.normal(0, 1, self.no_simulations)
            dw = dw_matrix[i - 1]
            simulations[i] = simulations[i - 1] * np.exp(
                (self.risk_free_rate - 0.5 * self.sigma ** 2) * self.dt + self.sigma * dw)
        return simulations

    def close_form_discounted_payoff(self):
        asset_path = self.close_from_asset_paths()
        european_call_payoff = np.maximum(asset_path - self.Strike, 0)
        european_option_discounted_value = np.mean(european_call_payoff[-1]) * self.discount
        binary_call_payoff = (asset_path > self.Strike).astype(float)
        binary_option_discounted_value = np.mean(binary_call_payoff[-1]) * self.discount
        return asset_path, european_call_payoff, binary_call_payoff, european_option_discounted_value, binary_option_discounted_value

    def black_scholes(self):
        d1 = (np.log(self.Spot / self.Strike) + (
                    self.risk_free_rate + 0.5 * self.sigma ** 2) * self.time_to_maturity) / (
                         self.sigma * np.sqrt(self.time_to_maturity))
        d2 = d1 - self.sigma * np.sqrt(self.time_to_maturity)
        european_call = self.Spot * norm.cdf(d1) - self.Strike * np.exp(
            -self.risk_free_rate * self.time_to_maturity) * norm.cdf(d2)
        binary_call = norm.cdf(d2) * np.exp(-self.risk_free_rate * self.time_to_maturity)
        return european_call, binary_call

    def error_analysis_table(self):
        euler_scheme = self.euler_discounted_payoff()
        milstein_scheme = self.milstein_discounted_payoff()
        close_form_scheme = self.close_form_discounted_payoff()
        black_scholes = self.black_scholes()
        z = 1.96  # confidence interval (95%)

        methods = ["Closed-form", "Euler", "Milstein"]
        option_type = ["EUROPEAN CALL", "BINARY CALL"]

        df_stats = pd.DataFrame(columns=["Simulation Number", "Method", "Number of Simulation", "Rate of Return(r %)",
                                         "Volatility(Sigma %)", "Option Type", "Simulated Price", "Black Scholes Price",
                                         "Absolute Error", "Standard Error", "Relative Error",
                                         "95% Confidence Interval", "CI Width"])

        for j in range(len(option_type)):
            for i in range(len(methods)):
                df_stats = df_stats._append({
                    "Simulation Number": self.simulation_count,
                    "Method": methods[i],
                    "Number of Simulation": self.no_simulations,
                    "Rate of Return(r %)": (self.risk_free_rate) * 100,
                    "Volatility(Sigma %)": (self.sigma) * 100,
                    "Option Type": option_type[j],
                    "Simulated Price": [None],
                    "Black Scholes Price": [None],
                    "Absolute Error": [None],
                    "Standard Error": [None],
                    "Relative Error": [None],
                    "CI Width": [None]
                }, ignore_index=True)

                scheme = {"Euler": euler_scheme, "Milstein": milstein_scheme, "Closed-form": close_form_scheme}[
                    methods[i]]
                payoff = scheme[3 + j]
                std_dev = np.std(scheme[1 + j][-1]) * self.discount / np.sqrt(self.no_simulations)
                if methods[i] == "Closed-form":
                    close_form_payoff = payoff
                if option_type[j] == "EUROPEAN CALL":
                    row_idx = i
                else:
                    row_idx = len(methods) + i

                df_stats.loc[row_idx, "Simulated Price"] = payoff
                df_stats.loc[row_idx, "Standard Error"] = std_dev
                df_stats.loc[row_idx, "Black Scholes Price"] = black_scholes[j]
                df_stats.loc[row_idx, "Absolute Error"] = close_form_payoff - payoff
                df_stats.loc[row_idx, "Relative Error"] = (df_stats.loc[
                                                               row_idx, "Absolute Error"] / close_form_payoff) * 100
                df_stats.loc[row_idx, "95% Confidence Interval"] = f"{payoff:.4f}+-{(z * std_dev):.4f}"
                df_stats.loc[row_idx, "CI Width"] = z * std_dev

        return df_stats, euler_scheme, milstein_scheme, close_form_scheme

    def simulation_plots(self):
        num_of_paths_to_plot = min(2000, self.no_simulations)
        method = self.error_analysis_table()

        plt.figure(figsize=(25, 12))

        schemes = {
            "Euler": (method[1][0], method[1][1:3], method[1][3:5]),
            "Milstein": (method[2][0], method[2][1:3], method[2][3:5]),
            "Closed-form": (method[3][0], method[3][1:3], method[3][3:5])
        }

        print("GENERATING PLOTS")
        for idx, (name, (asset_paths, option_paths, payoff)) in enumerate(tqdm(schemes.items(), desc="Plotting paths")):
            t = np.arange(asset_paths.shape[0])
            subset = slice(0, num_of_paths_to_plot)

            # asset path
            plt.subplot(2, 3, idx + 1)
            plt.plot(t, asset_paths[:, subset], alpha=0.5, linewidth=0.7)
            plt.plot(t, np.mean(asset_paths, axis=1), color='black', linewidth=2, label="Mean Stock Price Path")
            plt.title(f'{name} Scheme - Stock Price Paths')
            plt.xlabel('Time Steps')
            plt.ylabel('Stock Price')
            plt.legend()
            plt.grid(True)

            # Histograms for Final Asset Prices
            plt.subplot(2, 3, idx + 4)
            plt.hist(method[1][0][-1], bins=50)
            plt.title("Euler - Final Asset Prices")

            plt.subplot(2, 3, idx + 4)
            plt.hist(method[2][0][-1], bins=50)
            plt.title("Milstein - Final Asset Prices")

            plt.subplot(2, 3, idx + 4)
            plt.hist(method[3][0][-1], bins=50)
            plt.title("Closed-form - Final Asset Prices")

        plt.suptitle(f"SIMULATION Number {self.simulation_count} Vol = {self.sigma}, r = {self.risk_free_rate}",
                     fontsize=15, fontweight='bold')
        plt.show()

        return method[0]


if __name__ == "__main__":
    results = []
    simulation_count = 0
    simulation_len = [3000000, 1000000, 100000, 10000]
    risk_free_rates = [0.005, 0.02, 0.05]
    vols = [0.20, 0.40, 0.80]

    Z_full = np.random.normal(0, 1, (252, max(simulation_len)))  # shared randomness

    for ret in risk_free_rates:
        for vol in vols:
            for sims in simulation_len:
                Z = Z_full[:, :sims]  # use consistent randomness slice
                simulation_count += 1

                obj = PriceOption(
                    Spot=100,
                    Strike=100,
                    time_to_maturity=1,
                    dtt=252,
                    risk_free_rate=ret,
                    sigma=vol,
                    no_simulations=sims,
                    simulation_count=simulation_count,
                    Z_matrix=Z
                )


                if sims == max(simulation_len) and vol == max(vols) and (ret == max(risk_free_rates) or ret == min(risk_free_rates)) :
                    table=obj.simulation_plots()
                    results.append(table)
                elif sims == min(simulation_len) and vol ==min(vols) and (ret == max(risk_free_rates) or ret == min(risk_free_rates)):
                    table=obj.simulation_plots()
                    results.append(table)
                else:
                    table = obj.error_analysis_table()[0]
                    results.append(table)

    full_df = pd.concat(results, ignore_index=True)
    print(full_df)

    figure_count = 0
    methods = full_df["Method"].unique()
    option_types = full_df["Option Type"].unique()
    vols = sorted(full_df["Volatility(Sigma %)"].unique())
    returns = sorted(full_df["Rate of Return(r %)"].unique())

    plot_configs = [
        {
            "title": "Relative Error vs Number of Simulations",
            "x": "Number of Simulation", "y": "Relative Error",
            "ylabel": "Relative Error (%)", "xlabel": "Simulations (Millions)"
        },
        {
            "title": "Absolute Error vs Number of Simulations",
            "x": "Number of Simulation", "y": "Absolute Error",
            "ylabel": "Absolute Error", "xlabel": "Simulations (Millions)"
        }
    ]

    for plot in plot_configs:
        for option_type in option_types:
            n_subplots = len(vols) * len(returns)
            n_cols = 3
            n_rows = 3

            plt.figure(figsize=(16, n_rows * 4))
            plt.suptitle(f"{plot['title']} \nOption Type: {option_type}", fontsize=14, fontweight="bold")

            subplot_index = 1

            for vol in vols:
                for ret in returns:
                    plt.subplot(n_rows, n_cols, subplot_index)
                    figure_count += 1
                    for method in methods:
                        data = full_df[
                            (full_df["Method"] == method) &
                            (full_df["Option Type"] == option_type) &
                            (full_df["Volatility(Sigma %)"] == vol) &
                            (full_df["Rate of Return(r %)"] == ret)
                            ].copy()

                        data = data.sort_values(by=plot["x"])
                        x = data[plot["x"]]
                        y = data[plot["y"]]
                        plt.plot(x, y, marker='X', label=method)
                        # plt.

                    plt.title(f" Figure: {figure_count}   Vol = {vol}, r = {ret}", fontsize=11, fontweight="bold")
                    plt.xlabel(plot["xlabel"])
                    plt.ylabel(plot["ylabel"])

                    plt.grid(True)
                    plt.legend()
                    subplot_index += 1

            plt.tight_layout()
            plt.show()
