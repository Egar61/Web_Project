from flask import Flask, render_template_string, request, redirect, url_for
import json
import os
from collections import defaultdict
from datetime import datetime

app = Flask(__name__)

DATA_FILE = 'transactions.json'

PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Финансовый учет</title>
<style>
  body {
      font-family: Arial, sans-serif;
      max-width: 700px;
      margin: auto;
      padding: 15px;
      background: #f4f6f8;
      color: #333;
  }
  h1 { text-align: center; margin-bottom: 0.5em; }
  form {
    margin-bottom: 1em;
    background: white;
    padding: 1em;
    border-radius: 8px;
    box-shadow: 0 0 6px rgba(0,0,0,0.1);
  }
  label {
    display: block;
    margin-top: 10px;
    font-weight: bold;
  }
  input[type="number"], input[type="date"], select {
    width: 100%;
    padding: 6px;
    box-sizing: border-box;
    margin-top: 5px;
    border-radius: 5px;
    border: 1px solid #ccc;
  }
  button {
    margin-top: 15px;
    padding: 10px 15px;
    background-color: #007bff;
    color: white;
    border:none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 1em;
  }
  button:hover {
    background-color: #0056b3;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    background: white;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 0 6px rgba(0,0,0,0.1);
  }
  th, td {
    padding: 10px;
    border-bottom: 1px solid #e0e0e0;
    text-align: center;
  }
  th {
    background-color: #007bff;
    color: white;
    user-select: none;
  }
  tr:hover {
    background-color: #f1f1f1;
  }
  .container {
    margin-bottom: 30px;
  }
  nav {
    margin-bottom: 20px;
    text-align: center;
  }
  nav a {
    margin: 0 15px;
    text-decoration: none;
    font-weight: bold;
    color: #007bff;
  }
  nav a.active {
    color: #0056b3;
  }
  .hidden {
    display: none;
  }
  @media (max-width: 600px) {
    body {
      padding: 10px;
      max-width: 100%;
    }
    table, thead, tbody, th, td, tr {
      display: block;
    }
    th {
      position: absolute;
      left: -9999px;
    }
    tr {
      margin-bottom: 1em;
      border: 1px solid #ccc;
      border-radius: 8px;
      padding: 10px;
    }
    td {
      border: none;
      position: relative;
      padding-left: 50%;
      text-align: left;
    }
    td:before {
      position: absolute;
      left: 10px;
      width: 45%;
      white-space: nowrap;
      font-weight: bold;
    }
    td:nth-of-type(1):before { content: "Дата"; }
    td:nth-of-type(2):before { content: "Категория"; }
    td:nth-of-type(3):before { content: "Подкатегория"; }
    td:nth-of-type(4):before { content: "Сумма"; }
    td:nth-of-type(5):before { content: "Тип"; }
    td:nth-of-type(6):before { content: "Действия"; }
  }
  .details-popup {
    display: none;
    position: fixed;
    background: white;
    box-shadow: 0 0 15px rgba(0,0,0,0.3);
    padding: 15px;
    border-radius: 8px;
    top: 50%;
    left: 50%;
    max-width: 90%;
    max-height: 80%;
    overflow-y: auto;
    transform: translate(-50%, -50%);
    z-index: 1000;
  }
  .details-popup.active {
    display: block;
  }
  .details-popup h3 {
    margin-top: 0;
  }
  .details-popup button {
    background: #dc3545;
    margin-top: 10px;
  }
</style>
</head>
<body>
<h1>Финансовый учет</h1>
<nav>
  <a href="{{ url_for('index') }}" class="{{ 'active' if active_tab == 'transactions' else '' }}">Транзакции</a>
  <a href="{{ url_for('stats') }}" class="{{ 'active' if active_tab == 'stats' else '' }}">Статистика</a>
</nav>

{% if active_tab == 'transactions' %}
<div class="container">
  <form method="post" action="{{ url_for('add_transaction') }}">
    <label for="date">Дата:</label>
    <input type="date" id="date" name="date" value="{{ today }}" required />

    <label for="category">Категория:</label>
    <select id="category" name="category" required onchange="toggleExpenseCategory()">
      <option value="Доход" {% if selected_category == 'Доход' %}selected{% endif %}>Доход</option>
      <option value="Расход" {% if selected_category == 'Расход' %}selected{% endif %}>Расход</option>
    </select>

    <label for="expense_category" id="expense_category_label" class="{% if selected_category != 'Расход' %}hidden{% endif %}">Подкатегория расхода:</label>
    <select id="expense_category" name="expense_category" class="{% if selected_category != 'Расход' %}hidden{% endif %}">
      {% for cat in expense_categories %}
      <option value="{{ cat }}" {% if cat == selected_expense_category %}selected{% endif %}>{{ cat }}</option>
      {% endfor %}
    </select>

    <label for="amount">Сумма:</label>
    <input type="number" name="amount" id="amount" step="0.01" min="0" value="{{ amount|default('') }}" required />

    <button type="submit">Добавить</button>
  </form>
</div>

<div class="container">
  <h2>Список транзакций</h2>
  {% if transactions %}
  <table>
    <thead>
      <tr>
        <th>Дата</th>
        <th>Категория</th>
        <th>Подкатегория</th>
        <th>Сумма</th>
        <th>Тип</th>
        <th>Действия</th>
      </tr>
    </thead>
    <tbody>
      {% for t in transactions %}
      <tr>
        <td>{{ t.formatted_date }}</td>
        <td>{{ t.category }}</td>
        <td>{{ t.expense_category if t.category == 'Расход' else '—' }}</td>
        <td>{{ '%.2f' % t.amount }}</td>
        <td>{{ t.category }}</td>
        <td>
          <form method="post" action="{{ url_for('delete_transaction', index=loop.index0) }}" style="margin:0;">
            <button type="submit" onclick="return confirm('Удалить эту транзакцию?');">Удалить</button>
          </form>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p>Транзакций пока нет.</p>
  {% endif %}
</div>

<script>
  function toggleExpenseCategory() {
    const categorySelect = document.getElementById('category');
    const expenseCatSelect = document.getElementById('expense_category');
    const expenseLabel = document.getElementById('expense_category_label');
    if (categorySelect.value === 'Расход') {
      expenseCatSelect.classList.remove('hidden');
      expenseLabel.classList.remove('hidden');
      expenseCatSelect.required = true;
    } else {
      expenseCatSelect.classList.add('hidden');
      expenseLabel.classList.add('hidden');
      expenseCatSelect.required = false;
    }
  }
  window.onload = toggleExpenseCategory;
</script>

{% elif active_tab == 'stats' %}
<div class="container">
  <h2>Статистика по месяцам</h2>
  {% if monthly_stats %}
  <table>
    <thead>
      <tr>
        <th>Месяц</th>
        <th>Доходы</th>
        <th>Расходы</th>
        <th>Чистый доход/расход</th>
        <th>Детали расходов</th>
      </tr>
    </thead>
    <tbody>
      {% for month, data in monthly_stats.items() %}
      <tr>
        <td>{{ month }}</td>
        <td>{{ '%.2f' % data.income }}</td>
        <td>{{ '%.2f' % data.expense }}</td>
        <td>{{ '%.2f' % (data.income - data.expense) }}</td>
        <td><button onclick="showDetails('{{ month }}')">Показать</button></td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p>Данных для статистики пока нет.</p>
  {% endif %}
</div>

<div id="details-popup" class="details-popup">
  <h3>Детали расходов за <span id="details-month"></span></h3>
  <pre id="details-content"></pre>
  <button onclick="closeDetails()">Закрыть</button>
</div>

<script>
  const detailsData = {{ details_json | safe }};

  function showDetails(month) {
    document.getElementById('details-month').textContent = month;
    const contentEl = document.getElementById('details-content');
    if (detailsData[month]) {
      let text = '';
      for (const [category, amount] of Object.entries(detailsData[month])) {
        text += category + ': ' + amount.toFixed(2) + '\\n';
      }
      contentEl.textContent = text;
    } else {
      contentEl.textContent = 'Данные отсутствуют.';
    }
    document.getElementById('details-popup').classList.add('active');
  }

  function closeDetails() {
    document.getElementById('details-popup').classList.remove('active');
  }
</script>

{% endif %}
</body>
</html>
"""

ALLOWED_EXPENSE_CATEGORIES = {"Бензин", "Продукты", "Коммуналка", "Хозтовары", "Лекарства", "Досуг"}


def load_transactions():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            transactions = []
            for t in data:
                transactions.append({
                    "date": t.get("date"),
                    "category": t.get("category"),
                    "expense_category": t.get("expense_category", ""),
                    "amount": float(t.get("amount", 0)),
                })
            return transactions
        except Exception:
            return []


def save_transactions(transactions):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(transactions, f, ensure_ascii=False, indent=2)


def calculate_monthly_stats(transactions):
    monthly_stats = defaultdict(
        lambda: {"income": 0.0, "expense": 0.0, "categories": defaultdict(float)}
    )
    for t in transactions:
        try:
            dt = datetime.strptime(t["date"], "%Y-%m-%d")
            month_key = dt.strftime("%m.%Y")
            amount = float(t["amount"])
            if t["category"] == "Доход":
                monthly_stats[month_key]["income"] += amount
            else:
                if t["expense_category"] in ALLOWED_EXPENSE_CATEGORIES:
                    monthly_stats[month_key]["expense"] += amount
                    monthly_stats[month_key]["categories"][t["expense_category"]] += amount
                else:
                    monthly_stats[month_key]["expense"] += amount
        except Exception:
            continue
    return monthly_stats


def format_date_dd_mm_yyyy(date_str_iso):
    try:
        dt = datetime.strptime(date_str_iso, "%Y-%m-%d")
        return dt.strftime("%d:%m:%Y")
    except Exception:
        return date_str_iso


@app.route("/")
def index():
    transactions = load_transactions()
    for t in transactions:
        t["formatted_date"] = format_date_dd_mm_yyyy(t["date"])
    today = datetime.today().strftime("%Y-%m-%d")
    return render_template_string(
        PAGE_TEMPLATE,
        active_tab="transactions",
        transactions=transactions,
        today=today,
        selected_category="Доход",
        selected_expense_category=None,
        amount="",
        expense_categories=sorted(ALLOWED_EXPENSE_CATEGORIES),
    )


@app.route("/add", methods=["POST"])
def add_transaction():
    date = request.form.get("date")
    category = request.form.get("category")
    expense_category = request.form.get("expense_category") if category == "Расход" else ""
    if category == "Расход" and expense_category not in ALLOWED_EXPENSE_CATEGORIES:
        expense_category = ""
    try:
        amount = float(request.form.get("amount"))
    except (ValueError, TypeError):
        amount = 0.0
    if not date or not category or amount <= 0:
        return redirect(url_for("index"))
    transactions = load_transactions()
    transactions.append(
        {
            "date": date,
            "category": category,
            "expense_category": expense_category,
            "amount": amount,
        }
    )
    save_transactions(transactions)
    return redirect(url_for("index"))


@app.route("/delete/<int:index>", methods=["POST"])
def delete_transaction(index):
    transactions = load_transactions()
    if 0 <= index < len(transactions):
        del transactions[index]
        save_transactions(transactions)
    return redirect(url_for("index"))


@app.route("/stats")
def stats():
    transactions = load_transactions()
    monthly_stats = calculate_monthly_stats(transactions)

    class StatRow:
        def __init__(self, income, expense, categories):
            self.income = income
            self.expense = expense
            self.categories = categories

    stats_for_template = {
        month: StatRow(data["income"], data["expense"], data["categories"])
        for month, data in monthly_stats.items()
    }

    details_json = {
        m: {cat: amt for cat, amt in data["categories"].items()}
        for m, data in monthly_stats.items()
    }

    return render_template_string(
        PAGE_TEMPLATE,
        active_tab="stats",
        monthly_stats=stats_for_template,
        details_json=details_json,
    )


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
