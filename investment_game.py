#!/usr/bin/env python3
"""
Инвестиционная игра «Капитал: путь инвестора».

Что нового в этой версии:
- Более детальная макроэкономика: инфляция, ставка ЦБ, безработица, рост ВВП,
  потребительское доверие, режимы рынка (рост/рецессия/стагфляция/кризис).
- Микроэкономика игрока: риск потери работы, премии, экстренные расходы,
  рост зарплаты, стоимость обслуживания долга.
- Улучшенные механики портфеля: лимиты риска, целевая ребалансировка,
  журнал сделок и история денежных потоков.
- Отчётность и аналитика: CAGR, волатильность, Sharpe, Sortino, max drawdown,
  VaR 95%, структура доходности по источникам и сравнение с бенчмарком.
- Новости месяца: тематические новости, влияющие на макропоказатели
  и рынок (с вероятностями и амплитудами, близкими к реалистичным).

Запуск:
    python3 investment_game.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math
import random
import statistics


MONTHS = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


@dataclass
class Asset:
    symbol: str
    name: str
    asset_class: str
    price: float
    expected_annual_return: float
    annual_volatility: float
    expense_ratio: float = 0.0
    dividend_yield: float = 0.0
    coupon_yield: float = 0.0
    tax_rate_income: float = 0.13

    def monthly_expected_return(self) -> float:
        return (1 + self.expected_annual_return) ** (1 / 12) - 1

    def monthly_volatility(self) -> float:
        return self.annual_volatility / math.sqrt(12)

    def simulate_month(self, market_sentiment: float, rate_pressure: float, growth_pressure: float, risk_off: float) -> float:
        base = self.monthly_expected_return()
        vol = self.monthly_volatility()
        shock = random.gauss(0, vol)

        if self.asset_class == "bonds":
            sensitivity = -0.85 * rate_pressure + 0.25 * market_sentiment + 0.15 * risk_off
        elif self.asset_class == "stocks":
            sensitivity = 1.25 * market_sentiment - 0.45 * rate_pressure + 0.8 * growth_pressure - 1.1 * risk_off
        elif self.asset_class == "reit":
            sensitivity = 0.9 * market_sentiment - 0.9 * rate_pressure + 0.4 * growth_pressure - 0.7 * risk_off
        elif self.asset_class == "gold":
            sensitivity = -0.2 * market_sentiment + 0.7 * rate_pressure - 0.1 * growth_pressure + 1.0 * risk_off
        elif self.asset_class == "crypto":
            sensitivity = 1.9 * market_sentiment - 0.6 * rate_pressure + 0.9 * growth_pressure - 1.5 * risk_off
        else:
            sensitivity = 0.0

        gross_return = base + shock + sensitivity
        net_return = clamp(gross_return - self.expense_ratio / 12, -0.45, 0.45)
        self.price = max(0.1, self.price * (1 + net_return))
        return net_return


@dataclass
class Position:
    asset: Asset
    units: float
    avg_buy_price: float

    def market_value(self) -> float:
        return self.units * self.asset.price

    def unrealized_pnl(self) -> float:
        return self.units * (self.asset.price - self.avg_buy_price)


@dataclass
class Trade:
    month: int
    side: str
    symbol: str
    units: float
    price: float
    gross_value: float
    fee: float
    tax: float
    net_cash_flow: float


@dataclass
class MonthlySnapshot:
    month: int
    year: int
    nominal_net_worth: float
    real_net_worth: float
    portfolio_value: float
    cash: float
    debt: float
    passive_income: float
    salary_income: float
    expenses: float
    market_return: float
    macro_regime: str


@dataclass
class Economy:
    inflation_annual: float = 0.06
    central_bank_rate: float = 0.09
    unemployment: float = 0.055
    gdp_growth: float = 0.022
    consumer_confidence: float = 0.0
    market_sentiment: float = 0.0
    global_risk_index: float = 0.0
    month_index: int = 0
    year: int = 2026

    def regime(self) -> str:
        if self.inflation_annual > 0.09 and self.gdp_growth < 0.005:
            return "Стагфляция"
        if self.gdp_growth < -0.01 or self.unemployment > 0.095:
            return "Рецессия"
        if self.global_risk_index > 0.08:
            return "Кризисный риск"
        if self.gdp_growth > 0.02 and self.unemployment < 0.06:
            return "Рост"
        return "Нейтральный"

    def monthly_risk_free(self) -> float:
        return (1 + max(self.central_bank_rate - 0.01, 0.0)) ** (1 / 12) - 1

    def update(self) -> None:
        # Реалистичная связка показателей (без экстремальных скачков)
        inflation_shock = random.gauss(0, 0.0035)
        rate_reaction = 0.35 * (self.inflation_annual - 0.06) + random.gauss(0, 0.002)

        self.inflation_annual = clamp(self.inflation_annual + inflation_shock - 0.03 * self.gdp_growth, 0.005, 0.22)
        self.central_bank_rate = clamp(self.central_bank_rate + rate_reaction, 0.01, 0.27)

        labor_shock = random.gauss(0, 0.0018)
        self.unemployment = clamp(self.unemployment + labor_shock - 0.03 * self.gdp_growth, 0.02, 0.22)

        growth_shock = random.gauss(0, 0.003)
        self.gdp_growth = clamp(
            self.gdp_growth + growth_shock - 0.18 * max(self.central_bank_rate - 0.10, 0) - 0.10 * max(self.unemployment - 0.07, 0),
            -0.06,
            0.08,
        )

        conf_trend = 0.6 * self.gdp_growth - 0.5 * self.unemployment - 0.4 * max(self.inflation_annual - 0.07, 0)
        self.consumer_confidence = clamp(random.gauss(conf_trend, 0.02), -0.2, 0.2)

        self.global_risk_index = clamp(
            0.45 * max(self.unemployment - 0.07, 0)
            + 0.35 * max(self.inflation_annual - 0.08, 0)
            + 0.20 * random.random() * 0.1,
            0.0,
            0.2,
        )

        sentiment_core = 0.8 * self.gdp_growth + 0.5 * self.consumer_confidence - 0.7 * self.global_risk_index
        self.market_sentiment = clamp(random.gauss(sentiment_core, 0.03), -0.2, 0.2)

        self.month_index += 1
        if self.month_index >= 12:
            self.month_index = 0
            self.year += 1

    def current_month_name(self) -> str:
        return MONTHS[self.month_index]


class NewsEngine:
    def __init__(self) -> None:
        self.events: List[Tuple[str, float, float, float, float, float, float]] = [
            # (текст, Δставка, Δинфляция, Δрост ВВП, Δбезработица, Δсентимент, Δриск)
            ("ЦБ дал жёсткий сигнал: приоритет — борьба с инфляцией.", 0.004, -0.002, -0.002, 0.001, -0.015, 0.010),
            ("Инфляция замедляется быстрее ожиданий аналитиков.", -0.003, -0.004, 0.001, -0.0005, 0.012, -0.008),
            ("Глобальные цепочки поставок восстановились.", -0.001, -0.002, 0.003, -0.001, 0.010, -0.005),
            ("Ухудшение геополитики повышает премию за риск.", 0.001, 0.001, -0.003, 0.001, -0.020, 0.022),
            ("Сильный сезон корпоративной отчётности поддержал рынок.", 0.0, 0.0, 0.002, -0.0005, 0.018, -0.006),
            ("Банковский стресс: ужесточение кредитных стандартов.", 0.002, 0.001, -0.004, 0.002, -0.022, 0.025),
            ("Технологический прорыв повысил ожидания производительности.", 0.0, -0.001, 0.004, -0.001, 0.020, -0.004),
            ("Нефть подорожала, что усилило инфляционное давление.", 0.002, 0.003, -0.001, 0.0005, -0.012, 0.011),
            ("Рынок труда остывает, вакансий становится меньше.", -0.001, -0.001, -0.002, 0.002, -0.010, 0.010),
            ("Фискальные стимулы поддержали потребительский спрос.", 0.001, 0.001, 0.004, -0.001, 0.014, -0.003),
        ]

    def maybe_publish(self, economy: Economy) -> Optional[str]:
        if random.random() > 0.55:
            return None

        text, d_rate, d_infl, d_growth, d_unemp, d_sent, d_risk = random.choice(self.events)
        economy.central_bank_rate = clamp(economy.central_bank_rate + d_rate, 0.01, 0.27)
        economy.inflation_annual = clamp(economy.inflation_annual + d_infl, 0.005, 0.22)
        economy.gdp_growth = clamp(economy.gdp_growth + d_growth, -0.06, 0.08)
        economy.unemployment = clamp(economy.unemployment + d_unemp, 0.02, 0.22)
        economy.market_sentiment = clamp(economy.market_sentiment + d_sent, -0.2, 0.2)
        economy.global_risk_index = clamp(economy.global_risk_index + d_risk, 0.0, 0.2)
        return text


@dataclass
class Player:
    name: str
    cash: float
    monthly_income: float
    monthly_expenses: float
    risk_profile: str
    debt: float = 0.0
    emergency_fund_target_months: int = 6
    tax_rate_capital_gain: float = 0.13
    commission_rate: float = 0.0015
    salary_growth_annual: float = 0.05
    employment_stability: float = 0.97  # чем выше, тем меньше риск потерять доход
    portfolio: Dict[str, Position] = field(default_factory=dict)
    trades: List[Trade] = field(default_factory=list)
    snapshots: List[MonthlySnapshot] = field(default_factory=list)
    achieved_goal: bool = False

    def net_worth(self) -> float:
        return self.cash + self.portfolio_value() - self.debt

    def portfolio_value(self) -> float:
        return sum(pos.market_value() for pos in self.portfolio.values())

    def real_net_worth(self, cumulative_inflation: float) -> float:
        return self.net_worth() / max(cumulative_inflation, 1e-6)

    def weights(self) -> Dict[str, float]:
        total = self.portfolio_value()
        if total <= 1e-9:
            return {}
        return {sym: pos.market_value() / total for sym, pos in self.portfolio.items()}

    def leverage_ratio(self) -> float:
        assets = self.cash + self.portfolio_value()
        return self.debt / assets if assets > 0 else 0.0

    def apply_microeconomics(self, economy: Economy) -> Tuple[float, float, float, str]:
        """Возвращает (зарплата, расходы, экстренные, комментарий)."""
        inflation_monthly = (1 + economy.inflation_annual) ** (1 / 12) - 1
        self.monthly_expenses *= (1 + inflation_monthly)

        salary_comment = ""
        # Вероятность временной потери дохода растёт при безработице
        layoff_probability = clamp((economy.unemployment - 0.045) * 1.8 + (1 - self.employment_stability) * 0.8, 0.0, 0.35)
        salary = self.monthly_income
        if random.random() < layoff_probability * 0.25:
            salary *= random.uniform(0.3, 0.6)
            salary_comment = "⚠️ Доход временно снизился из-за охлаждения рынка труда."

        # Годовой пересмотр зарплаты
        if random.random() < 1 / 12:
            adjustment = ((1 + self.salary_growth_annual) ** (1 / 12) - 1) + random.gauss(0, 0.004)
            self.monthly_income = max(30_000, self.monthly_income * (1 + adjustment))

        # Премия чаще в сильной экономике
        bonus = 0.0
        if economy.gdp_growth > 0.02 and random.random() < 0.20:
            bonus = self.monthly_income * random.uniform(0.15, 0.45)

        emergency = 0.0
        if random.random() < 0.08:
            emergency = self.monthly_expenses * random.uniform(0.35, 1.2)

        # Обслуживание долга
        debt_interest = self.debt * ((1 + (economy.central_bank_rate + 0.04)) ** (1 / 12) - 1)
        self.debt += debt_interest

        total_salary = salary + bonus
        total_out = self.monthly_expenses + emergency
        self.cash += total_salary - total_out

        if self.cash < 0:
            # автоматически уходим в долг
            self.debt += abs(self.cash)
            self.cash = 0.0

        return total_salary, total_out, emergency, salary_comment

    def add_income_from_assets(self) -> float:
        net_income = 0.0
        for pos in self.portfolio.values():
            income = pos.market_value() * ((pos.asset.dividend_yield + pos.asset.coupon_yield) / 12)
            if income <= 0:
                continue
            tax = income * pos.asset.tax_rate_income
            net_income += income - tax
        self.cash += net_income
        return net_income

    def buy(self, asset: Asset, amount_money: float, month: int) -> str:
        if amount_money <= 0:
            return "Сумма покупки должна быть больше 0."
        fee = amount_money * self.commission_rate
        total_cost = amount_money + fee
        if total_cost > self.cash:
            return "Недостаточно средств на счёте."

        units = amount_money / asset.price
        self.cash -= total_cost

        if asset.symbol in self.portfolio:
            p = self.portfolio[asset.symbol]
            total_units = p.units + units
            p.avg_buy_price = (p.avg_buy_price * p.units + asset.price * units) / total_units
            p.units = total_units
        else:
            self.portfolio[asset.symbol] = Position(asset=asset, units=units, avg_buy_price=asset.price)

        self.trades.append(
            Trade(month=month, side="BUY", symbol=asset.symbol, units=units, price=asset.price,
                  gross_value=amount_money, fee=fee, tax=0.0, net_cash_flow=-total_cost)
        )
        return f"Куплено {units:.4f} {asset.symbol} на {amount_money:,.2f} (комиссия {fee:,.2f})."

    def sell(self, asset: Asset, units: float, month: int) -> str:
        if units <= 0:
            return "Количество должно быть больше 0."
        if asset.symbol not in self.portfolio:
            return "У вас нет этого актива."

        p = self.portfolio[asset.symbol]
        if units > p.units:
            return "Недостаточно единиц для продажи."

        gross = units * asset.price
        fee = gross * self.commission_rate
        gain = units * (asset.price - p.avg_buy_price)
        tax = max(0.0, gain * self.tax_rate_capital_gain)
        net = gross - fee - tax

        self.cash += net
        p.units -= units
        if p.units <= 1e-8:
            del self.portfolio[asset.symbol]

        self.trades.append(
            Trade(month=month, side="SELL", symbol=asset.symbol, units=units, price=asset.price,
                  gross_value=gross, fee=fee, tax=tax, net_cash_flow=net)
        )
        return f"Продано {units:.4f} {asset.symbol}, зачислено {net:,.2f} (комиссия {fee:,.2f}, налог {tax:,.2f})."


class InvestmentGame:
    def __init__(self) -> None:
        self.economy = Economy()
        self.news = NewsEngine()
        self.assets = self._create_assets()

        self.cumulative_inflation = 1.0
        self.month_counter = 0

        self.target_real_capital = 2_500_000
        self.max_months = 120
        self.player: Optional[Player] = None
        self.benchmark_history: List[float] = [1.0]

    def _create_assets(self) -> Dict[str, Asset]:
        return {
            "CASH": Asset("CASH", "Денежный рынок", "cash", 1.0, 0.065, 0.004, expense_ratio=0.001),
            "BOND": Asset("BOND", "ОФЗ/облигации", "bonds", 100.0, 0.095, 0.08, expense_ratio=0.002, coupon_yield=0.085),
            "EQTY": Asset("EQTY", "Индекс акций", "stocks", 50.0, 0.14, 0.24, expense_ratio=0.004, dividend_yield=0.024),
            "REIT": Asset("REIT", "Фонд недвижимости", "reit", 40.0, 0.115, 0.20, expense_ratio=0.005, dividend_yield=0.05),
            "GOLD": Asset("GOLD", "Золото", "gold", 30.0, 0.08, 0.16, expense_ratio=0.003),
            "CRYP": Asset("CRYP", "Крипто-индекс", "crypto", 20.0, 0.2, 0.58, expense_ratio=0.010),
        }

    def _choose_risk_profile(self) -> str:
        print("\nПрофиль риска:")
        print("1) Консервативный")
        print("2) Сбалансированный")
        print("3) Агрессивный")
        while True:
            c = input("Выберите 1/2/3: ").strip()
            if c == "1":
                return "conservative"
            if c == "2":
                return "balanced"
            if c == "3":
                return "aggressive"
            print("Неверный выбор.")

    def setup_player(self) -> None:
        print("\n=== КАПИТАЛ: ПУТЬ ИНВЕСТОРА 2.0 ===")
        print("Цель: достичь реального капитала 2.5 млн за 10 лет.")

        name = input("Введите имя инвестора: ").strip() or "Игрок"

        def read_pos(prompt: str, min_value: float = 0.0) -> float:
            while True:
                try:
                    x = float(input(prompt).replace(" ", ""))
                    if x < min_value:
                        raise ValueError
                    return x
                except ValueError:
                    print("Введите корректное число.")

        start_cash = read_pos("Стартовый капитал (например, 300000): ", 1)
        income = read_pos("Ежемесячный доход после налогов (например, 120000): ", 1)
        expenses = read_pos("Ежемесячные расходы (например, 70000): ", 0)
        risk_profile = self._choose_risk_profile()

        stability = 0.97 if risk_profile == "conservative" else 0.95 if risk_profile == "balanced" else 0.92
        self.player = Player(
            name=name,
            cash=start_cash,
            monthly_income=income,
            monthly_expenses=expenses,
            risk_profile=risk_profile,
            employment_stability=stability,
        )

    def run(self) -> None:
        self.setup_player()
        assert self.player is not None

        while self.month_counter < self.max_months:
            self.month_counter += 1
            self._simulate_month()
            if self._check_game_over():
                break
            self._player_turn()
            if self._check_game_over():
                break
            self.economy.update()

        self._final_report()

    def _simulate_month(self) -> None:
        assert self.player is not None

        # 1) Инфляция и микроэкономика игрока
        infl_monthly = (1 + self.economy.inflation_annual) ** (1 / 12) - 1
        self.cumulative_inflation *= (1 + infl_monthly)
        salary_income, total_expenses, emergency, salary_comment = self.player.apply_microeconomics(self.economy)

        # 2) Пассивный доход
        passive_income = self.player.add_income_from_assets()

        # 3) Новости
        news_text = self.news.maybe_publish(self.economy)

        # 4) Рынок
        rate_pressure = self.economy.central_bank_rate - 0.08
        growth_pressure = self.economy.gdp_growth - 0.02
        risk_off = self.economy.global_risk_index

        market_returns: Dict[str, float] = {}
        for sym, a in self.assets.items():
            if sym == "CASH":
                r = self.economy.monthly_risk_free() - a.expense_ratio / 12
                a.price *= (1 + r)
                market_returns[sym] = r
            else:
                market_returns[sym] = a.simulate_month(self.economy.market_sentiment, rate_pressure, growth_pressure, risk_off)

        # 5) Бенчмарк 60/40
        benchmark_r = 0.6 * market_returns.get("EQTY", 0) + 0.4 * market_returns.get("BOND", 0)
        self.benchmark_history.append(self.benchmark_history[-1] * (1 + benchmark_r))

        # 6) Снимок и вывод
        self._record_snapshot(passive_income, salary_income, total_expenses, benchmark_r)
        self._show_status(news_text, salary_comment, emergency)

    def _record_snapshot(self, passive_income: float, salary_income: float, expenses: float, benchmark_r: float) -> None:
        assert self.player is not None
        self.player.snapshots.append(
            MonthlySnapshot(
                month=self.economy.month_index + 1,
                year=self.economy.year,
                nominal_net_worth=self.player.net_worth(),
                real_net_worth=self.player.real_net_worth(self.cumulative_inflation),
                portfolio_value=self.player.portfolio_value(),
                cash=self.player.cash,
                debt=self.player.debt,
                passive_income=passive_income,
                salary_income=salary_income,
                expenses=expenses,
                market_return=benchmark_r,
                macro_regime=self.economy.regime(),
            )
        )

    def _show_status(self, news_text: Optional[str], salary_comment: str, emergency: float) -> None:
        assert self.player is not None
        nw = self.player.net_worth()
        real = self.player.real_net_worth(self.cumulative_inflation)
        weights = self.player.weights()

        print("\n" + "=" * 84)
        print(f"{self.economy.current_month_name()} {self.economy.year} | Месяц {self.month_counter}/{self.max_months}")
        print(f"Режим экономики: {self.economy.regime()}")
        print(
            f"Инфляция: {self.economy.inflation_annual*100:5.2f}% | Ставка ЦБ: {self.economy.central_bank_rate*100:5.2f}% | "
            f"Безработица: {self.economy.unemployment*100:5.2f}%"
        )
        print(
            f"Рост ВВП: {self.economy.gdp_growth*100:5.2f}% | Доверие: {self.economy.consumer_confidence*100:5.2f}% | "
            f"Глобальный риск: {self.economy.global_risk_index*100:5.2f}%"
        )
        if news_text:
            print(f"\n📰 Новость месяца: {news_text}")
        if salary_comment:
            print(salary_comment)
        if emergency > 0:
            print(f"⚠️ Экстренные траты: {emergency:,.2f}")

        print("-" * 84)
        print(f"Кэш: {self.player.cash:,.2f} | Долг: {self.player.debt:,.2f} | Леверидж: {self.player.leverage_ratio()*100:,.2f}%")
        print(f"Капитал (номинал): {nw:,.2f}")
        print(f"Капитал (реальный): {real:,.2f} | Цель: {self.target_real_capital:,.2f}")

        if self.player.portfolio:
            print("\nПортфель:")
            print(f"{'Тикер':<6} {'Доля':>8} {'Ед.':>12} {'Цена':>11} {'Стоимость':>14} {'P/L':>12}")
            for sym, pos in sorted(self.player.portfolio.items()):
                w = weights.get(sym, 0.0)
                print(f"{sym:<6} {w*100:>7.2f}% {pos.units:>12.4f} {pos.asset.price:>11.2f} {pos.market_value():>14,.2f} {pos.unrealized_pnl():>12,.2f}")
        else:
            print("\nПортфель пока пуст.")

        print("\nДоступные активы:")
        for sym, a in self.assets.items():
            print(
                f"- {sym}: {a.name} | Цена: {a.price:,.2f} | ER: {a.expense_ratio*100:.2f}% | "
                f"Ожид. доходн.(г): {a.expected_annual_return*100:.1f}% | Волатильность(г): {a.annual_volatility*100:.1f}%"
            )

    def _player_turn(self) -> None:
        assert self.player is not None
        while True:
            print("\nДействия: [buy], [sell], [rebalance], [analyze], [skip]")
            action = input("Ваш выбор: ").strip().lower()
            if action in ("", "skip"):
                return
            if action == "buy":
                self._action_buy()
            elif action == "sell":
                self._action_sell()
            elif action == "rebalance":
                self._action_rebalance()
            elif action == "analyze":
                self._print_short_analytics()
            else:
                print("Неизвестная команда.")
                continue

            if input("Ещё действие в этом месяце? (y/n): ").strip().lower() != "y":
                return

    def _action_buy(self) -> None:
        assert self.player is not None
        sym = input("Тикер: ").strip().upper()
        asset = self.assets.get(sym)
        if not asset:
            print("Неизвестный тикер.")
            return
        try:
            amount = float(input("Сумма покупки: ").replace(" ", ""))
        except ValueError:
            print("Неверная сумма.")
            return

        # Ограничитель рискованного актива
        risky = {"CRYP"}
        if sym in risky:
            current_weight = self.player.weights().get(sym, 0.0)
            if self.player.risk_profile == "conservative" and current_weight > 0.05:
                print("Лимит риска: для консервативного профиля доля CRYP не должна превышать ~5%.")
                return
            if self.player.risk_profile == "balanced" and current_weight > 0.12:
                print("Лимит риска: для сбалансированного профиля доля CRYP не должна превышать ~12%.")
                return

        print(self.player.buy(asset, amount, self.month_counter))

    def _action_sell(self) -> None:
        assert self.player is not None
        sym = input("Тикер: ").strip().upper()
        asset = self.assets.get(sym)
        if not asset:
            print("Неизвестный тикер.")
            return
        try:
            units = float(input("Количество для продажи: ").replace(" ", ""))
        except ValueError:
            print("Неверное количество.")
            return

        print(self.player.sell(asset, units, self.month_counter))

    def _suggest_target_weights(self) -> Dict[str, float]:
        assert self.player is not None
        regime = self.economy.regime()

        if self.player.risk_profile == "conservative":
            base = {"CASH": 0.20, "BOND": 0.45, "EQTY": 0.20, "REIT": 0.08, "GOLD": 0.07}
        elif self.player.risk_profile == "balanced":
            base = {"CASH": 0.10, "BOND": 0.25, "EQTY": 0.40, "REIT": 0.12, "GOLD": 0.08, "CRYP": 0.05}
        else:
            base = {"CASH": 0.05, "BOND": 0.15, "EQTY": 0.45, "REIT": 0.12, "GOLD": 0.08, "CRYP": 0.15}

        # Макро-адаптация
        if regime in ("Рецессия", "Кризисный риск"):
            base["BOND"] = base.get("BOND", 0) + 0.08
            base["EQTY"] = max(base.get("EQTY", 0) - 0.06, 0.05)
            base["CRYP"] = max(base.get("CRYP", 0) - 0.02, 0.0)
            base["CASH"] = base.get("CASH", 0) + 0.02
        elif regime == "Стагфляция":
            base["GOLD"] = base.get("GOLD", 0) + 0.04
            base["BOND"] = max(base.get("BOND", 0) - 0.03, 0.1)

        total = sum(base.values())
        return {k: v / total for k, v in base.items()}

    def _action_rebalance(self) -> None:
        assert self.player is not None
        target = self._suggest_target_weights()
        print("Рекомендуемые доли с учётом профиля и макро-режима:")
        for sym, w in target.items():
            print(f"- {sym}: {w*100:.1f}%")

        if input("Выполнить авто-ребаланс? (y/n): ").strip().lower() != "y":
            return

        total = self.player.cash + self.player.portfolio_value()

        # Продажи
        for sym, pos in list(self.player.portfolio.items()):
            desired = total * target.get(sym, 0)
            current = pos.market_value()
            if current > desired:
                value_to_sell = current - desired
                units = min(pos.units, value_to_sell / pos.asset.price)
                if units > 1e-6:
                    print(self.player.sell(pos.asset, units, self.month_counter))

        # Покупки
        for sym, w in target.items():
            asset = self.assets[sym]
            desired = total * w
            current = self.player.portfolio.get(sym).market_value() if sym in self.player.portfolio else 0.0
            diff = desired - current
            amount = min(diff, self.player.cash * 0.995)
            if amount > 500:
                print(self.player.buy(asset, amount, self.month_counter))

    def _portfolio_real_returns(self) -> List[float]:
        assert self.player is not None
        if len(self.player.snapshots) < 2:
            return []
        rr = []
        for prev, cur in zip(self.player.snapshots[:-1], self.player.snapshots[1:]):
            if prev.real_net_worth > 0:
                rr.append(cur.real_net_worth / prev.real_net_worth - 1)
        return rr

    def _benchmark_returns(self) -> List[float]:
        if len(self.benchmark_history) < 2:
            return []
        return [b / a - 1 for a, b in zip(self.benchmark_history[:-1], self.benchmark_history[1:])]

    def _compute_analytics(self) -> Dict[str, float]:
        assert self.player is not None
        returns = self._portfolio_real_returns()
        if not returns:
            return {}

        mean_m = statistics.fmean(returns)
        vol_m = statistics.pstdev(returns) if len(returns) > 1 else 0.0
        neg = [r for r in returns if r < 0]
        downside = statistics.pstdev(neg) if len(neg) > 1 else 0.0
        rf = self.economy.monthly_risk_free()

        cumulative = 1.0
        for r in returns:
            cumulative *= (1 + r)
        months = len(returns)

        cagr = cumulative ** (12 / months) - 1
        vol_a = vol_m * math.sqrt(12)
        sharpe = ((mean_m - rf) / vol_m * math.sqrt(12)) if vol_m > 1e-12 else 0.0
        sortino = ((mean_m - rf) / downside * math.sqrt(12)) if downside > 1e-12 else 0.0

        # Max drawdown по реальному капиталу
        path = [s.real_net_worth for s in self.player.snapshots]
        peak = path[0]
        max_dd = 0.0
        for x in path:
            peak = max(peak, x)
            max_dd = max(max_dd, (peak - x) / peak if peak > 0 else 0.0)

        # VaR 95 (месячный)
        sorted_r = sorted(returns)
        idx = max(0, int(0.05 * len(sorted_r)) - 1)
        var95 = abs(sorted_r[idx])

        # Альфа относительно бенчмарка (грубая)
        bm = self._benchmark_returns()
        bm_mean = statistics.fmean(bm) if bm else 0.0
        alpha_m = mean_m - bm_mean

        return {
            "cagr_real": cagr,
            "vol_annual": vol_a,
            "sharpe": sharpe,
            "sortino": sortino,
            "max_drawdown": max_dd,
            "var95_monthly": var95,
            "alpha_annual": alpha_m * 12,
        }

    def _print_short_analytics(self) -> None:
        stats = self._compute_analytics()
        if not stats:
            print("Недостаточно данных для аналитики (нужно минимум 2 месяца).")
            return

        print("\nАналитика портфеля:")
        print(f"- CAGR (реальный): {stats['cagr_real']*100:,.2f}%")
        print(f"- Волатильность (годовая): {stats['vol_annual']*100:,.2f}%")
        print(f"- Sharpe: {stats['sharpe']:,.2f}")
        print(f"- Sortino: {stats['sortino']:,.2f}")
        print(f"- Max Drawdown: {stats['max_drawdown']*100:,.2f}%")
        print(f"- VaR 95% (месячный): {stats['var95_monthly']*100:,.2f}%")
        print(f"- Alpha vs 60/40 (годовая): {stats['alpha_annual']*100:,.2f}%")

    def _check_game_over(self) -> bool:
        assert self.player is not None
        real = self.player.real_net_worth(self.cumulative_inflation)
        if real >= self.target_real_capital:
            self.player.achieved_goal = True
            return True
        if self.player.debt > 1_500_000:
            print("\nКритический долг: финансовая устойчивость потеряна. Игра окончена.")
            return True
        return False

    def _final_report(self) -> None:
        assert self.player is not None
        stats = self._compute_analytics()

        print("\n" + "#" * 84)
        print("ФИНАЛЬНЫЙ ОТЧЁТ")
        print("#" * 84)
        print(f"Игрок: {self.player.name}")
        print(f"Период: {self.month_counter} месяцев")
        print(f"Финальный капитал (номинал): {self.player.net_worth():,.2f}")
        print(f"Финальный капитал (реальный): {self.player.real_net_worth(self.cumulative_inflation):,.2f}")
        print(f"Финальный долг: {self.player.debt:,.2f}")

        if stats:
            print("\nРиск и доходность:")
            print(f"- CAGR (реальный): {stats['cagr_real']*100:,.2f}%")
            print(f"- Волатильность (годовая): {stats['vol_annual']*100:,.2f}%")
            print(f"- Sharpe: {stats['sharpe']:,.2f}")
            print(f"- Sortino: {stats['sortino']:,.2f}")
            print(f"- Max Drawdown: {stats['max_drawdown']*100:,.2f}%")
            print(f"- VaR 95% (месячный): {stats['var95_monthly']*100:,.2f}%")
            print(f"- Alpha vs 60/40 (годовая): {stats['alpha_annual']*100:,.2f}%")

        total_fees = sum(t.fee for t in self.player.trades)
        total_taxes = sum(t.tax for t in self.player.trades)
        total_trades = len(self.player.trades)

        passive = sum(s.passive_income for s in self.player.snapshots)
        salary = sum(s.salary_income for s in self.player.snapshots)
        expenses = sum(s.expenses for s in self.player.snapshots)

        print("\nДенежные потоки:")
        print(f"- Доход от работы: {salary:,.2f}")
        print(f"- Пассивный доход: {passive:,.2f}")
        print(f"- Расходы домохозяйства: {expenses:,.2f}")
        print(f"- Сделок: {total_trades}, комиссии: {total_fees:,.2f}, налоги на сделки: {total_taxes:,.2f}")

        # Мини-новостной дайджест режимов
        regime_counts: Dict[str, int] = {}
        for s in self.player.snapshots:
            regime_counts[s.macro_regime] = regime_counts.get(s.macro_regime, 0) + 1

        if regime_counts:
            print("\nМакро-дайджест периода:")
            for k, v in sorted(regime_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"- {k}: {v} мес.")

        if self.player.achieved_goal:
            print("\n🏆 Поздравляем! Цель по реальному капиталу достигнута.")
        else:
            print("\nЦель не достигнута. Попробуйте снизить просадки и улучшить ребалансировку.")


def main() -> None:
    random.seed()
    game = InvestmentGame()
    game.run()


if __name__ == "__main__":
    main()
