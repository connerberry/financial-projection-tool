from flask import Flask, render_template, request
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Get user inputs from the form
        starting_salary = float(request.form['starting_salary'])
        starting_expenses = float(request.form['starting_expenses'])
        num_years = int(request.form['num_years'])
        num_children = int(request.form['num_children'])
        
        # Additional parameters
        yearly_wage_growth_rate = 1.07  # Placeholder - can make it user-input as well
        yearly_inflation_rate = 1.03
        market_rate = 1.1
        market_rate_in_retirement = 1.05
        age_first_child = 30
        yrs_between_kids = 2
        cost_per_child_per_year = 8500
        employer_401k_match = 0.06
        irs_401k_limit = 23000
        income_tax_rate = 0.22
        lifespan = 90
        expenses_in_retirement = 0.8

        # Run your financial projection logic
        data = run_financial_projection(
            starting_salary, starting_expenses, num_years, num_children, 
            yearly_wage_growth_rate, yearly_inflation_rate, market_rate, market_rate_in_retirement,
            age_first_child, yrs_between_kids, cost_per_child_per_year,
            employer_401k_match, irs_401k_limit, income_tax_rate, lifespan, expenses_in_retirement
        )
        
        # Generate a plot
        img = generate_plot(data)

        # Pass zip to the template
        return render_template('index.html', img_data=img, data=data, zip=zip)
    
    return render_template('index.html')

def run_financial_projection(
        starting_salary, starting_expenses, num_years, num_children, 
        yearly_wage_growth_rate, yearly_inflation_rate, market_rate, market_rate_in_retirement,
        age_first_child, yrs_between_kids, cost_per_child_per_year,
        employer_401k_match, irs_401k_limit, income_tax_rate, lifespan, expenses_in_retirement):
    
    principal = 0  # Starting portfolio
    inflation_discount = 1 / yearly_inflation_rate  # Inflation discount calculation
    portfolio = 0 + principal  # Holds the value of the portfolio
    final_salary = starting_salary  # Stores the salary at the end of each year
    starting_age = 23
    starting_year = 2025

    data = {
        'Year': [],
        'Age': [],
        'Salary': [],
        'Expenses': [],
        'Contribution': [],
        'Portfolio': [],
        "Portfolio in Today's Dollars": [],
    }

    # Calculations for the active working years
    for i in range(num_years):
        # CALCULATES WAGE GROWTH (change to be more gradual??)
        corrected_wage_growth_rate = yearly_wage_growth_rate  # Wage growth is initially set to the starting value
        if i == 0:
            corrected_wage_growth_rate = 1  # Starting wage
        if i > 9:
            corrected_wage_growth_rate = (yearly_wage_growth_rate - 1) / 2 + 1  # After 10 years, wage growth slows to half the initial rate (including inflation)
        if i > 14:
            corrected_wage_growth_rate = yearly_inflation_rate  # After 15 years, wage growth stalls to keeping up with inflation
        
        final_salary *= corrected_wage_growth_rate  # Final salary calculated for the current year

        # CALCULATES YEARLY EXPENSES
        age = starting_age + i
        yearly_expenses = starting_expenses * (yearly_inflation_rate ** i)  # Base expenses with growth rate, adjusted for inflation
        yearly_cost_kids = 0  # Cost of kids in this year
        
        # Iterates through all children
        if age > age_first_child:
            for kid_num in range(num_children):
                # Calculate the age of each child
                age_of_child = age - (age_first_child + kid_num * yrs_between_kids)
                
                # If the child is under 18, add their cost to yearly expenses
                if 0 <= age_of_child < 18:
                    yearly_cost_kids += cost_per_child_per_year * (yearly_inflation_rate ** i)
        
        # Add the cost of the kids to yearly expenses
        yearly_expenses += yearly_cost_kids
        
        # CALCULATES FINAL CONTRIBUTION AND PORTFOLIO VALUE
        employer_contribution = employer_401k_match * final_salary
        inflation_adjusted_401k_limit = irs_401k_limit * (yearly_inflation_rate ** i)
        potential_contribution = final_salary - yearly_expenses
        
        if potential_contribution > inflation_adjusted_401k_limit:  # Taxes income past the IRS 401k limit
            total_contribution = inflation_adjusted_401k_limit + (potential_contribution - inflation_adjusted_401k_limit) * income_tax_rate + employer_contribution
        else:  # If contribution is less than IRS 401k limit, contribution not taxed
            total_contribution = potential_contribution + employer_contribution
        
        portfolio = total_contribution + (portfolio * market_rate)  # Updates portfolio with contributions and returns
        
        # ADD INFO TO DATA
        data['Year'].append(starting_year + i)
        data['Age'].append(age)
        data['Salary'].append(final_salary)
        data['Expenses'].append(yearly_expenses)
        data['Contribution'].append(total_contribution)
        data['Portfolio'].append(max(portfolio, 0))
        data["Portfolio in Today's Dollars"].append(portfolio * (inflation_discount ** i))
    
    # CALCULATE RETIREMENT UTILIZATION
    for i in range(num_years, lifespan - starting_age):
        inflation_adjusted_expenses = (starting_expenses * (yearly_inflation_rate ** i)) * expenses_in_retirement  # Expenses adjusted for inflation
        
        portfolio -= inflation_adjusted_expenses
        portfolio *= market_rate_in_retirement
        
        data['Year'].append(starting_year + i)
        data['Age'].append(starting_age + i)
        data['Salary'].append(0)
        data['Expenses'].append(inflation_adjusted_expenses)
        data['Contribution'].append(0)
        data['Portfolio'].append(max(portfolio, 0))
        data["Portfolio in Today's Dollars"].append(portfolio * (inflation_discount ** i))
    
    return data

def generate_plot(data):
    # Convert data to DataFrame
    df = pd.DataFrame(data)

    # Generate plot
    plt.figure(figsize=(10, 6))
    plt.plot(df['Year'], df['Portfolio'], label="Portfolio")
    plt.plot(df['Year'], df['Salary'], label="Salary")
    plt.plot(df['Year'], df['Expenses'], label="Expenses")
    plt.xlabel('Year')
    plt.ylabel('Value')
    plt.title('Financial Projections Over Time')
    plt.legend()

    # Convert plot to PNG image
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()
    
    return plot_url

if __name__ == '__main__':
    app.run(debug=True)
