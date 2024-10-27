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
        principal = float(request.form['principal'])
        yearly_wage_growth_rate = float(request.form['yearly_wage_growth_rate'])
        yearly_inflation_rate = float(request.form['yearly_inflation_rate'])
        market_rate = float(request.form['market_rate'])
        market_rate_in_retirement = float(request.form['market_rate_in_retirement'])
        starting_salary = float(request.form['starting_salary'])
        starting_expenses = float(request.form['starting_expenses'])
        expenses_growth_rate = float(request.form['expenses_growth_rate'])
        starting_year = int(request.form['starting_year'])
        starting_age = int(request.form['starting_age'])
        num_years = int(request.form['num_years'])
        num_children = int(request.form['num_children'])
        age_first_child = int(request.form['age_first_child'])
        yrs_between_kids = int(request.form['yrs_between_kids'])
        cost_per_child_per_year = float(request.form['cost_per_child_per_year'])
        employer_401k_match = float(request.form['employer_401k_match'])
        lifespan = int(request.form['lifespan'])
        expenses_in_retirement = float(request.form['expenses_in_retirement'])
        expense_growth_retirement = float(request.form['expense_growth_retirement'])

        # Run your financial projection logic
        data = run_financial_projection(
            principal, yearly_wage_growth_rate, yearly_inflation_rate, market_rate, market_rate_in_retirement, starting_salary, starting_expenses, expenses_growth_rate, starting_year, starting_age, num_years, num_children, age_first_child, yrs_between_kids, cost_per_child_per_year, employer_401k_match, lifespan, expenses_in_retirement, expense_growth_retirement
        )
        
        # Generate a plot
        img = generate_plot(data)

        # Pass zip to the template
        return render_template('index.html', img_data=img, data=data, zip=zip)
    
    return render_template('index.html')

def run_financial_projection(
        principal, yearly_wage_growth_rate, yearly_inflation_rate, market_rate, market_rate_in_retirement, starting_salary, starting_expenses, expenses_growth_rate, starting_year, starting_age, num_years, num_children, age_first_child, yrs_between_kids, cost_per_child_per_year, employer_401k_match, lifespan, expenses_in_retirement, expense_growth_retirement):
    
    inflation_discount = 1 / yearly_inflation_rate
    portfolio = 0 + principal
    current_salary = starting_salary

    data = {
        'Year': [],
        'Age': [],
        'Salary': [],
        'Expenses': [],
        'Contribution': [],
        'Portfolio': [],
        "Portfolio in Today's Dollars": [],
    }

    for i in range(0,num_years): # Calculations all include inflation!
        # CALCULATES WAGE GROWTH (change to be more gradual??)
        corrected_wage_growth_rate = yearly_wage_growth_rate # Wage growth is initially set to the starting value
        if (i == 0): 
            corrected_wage_growth_rate = 1 # Wage growth starts at initial value
        if (i > 9):
            corrected_wage_growth_rate = (yearly_wage_growth_rate - 1)/2 + 1 # After 10 years, wage growth slows to half the initial rate (including inflation)
        if (i > 14):
            corrected_wage_growth_rate = yearly_inflation_rate # After 15 years, wage growth stalls to keeping up with inflation
            
        current_salary *= corrected_wage_growth_rate # Final salary calculated for the current year in this iteration
        
        
        # CALCULATES YEARLY EXPENSES
        age = starting_age + i
        yearly_expenses = starting_expenses * (yearly_inflation_rate ** i) * (expenses_growth_rate ** i)  # Base expenses with growth rate, adjusted for inflation
        
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
        employer_contribution = employer_401k_match * (current_salary * employer_401k_match) # Assumes equal match
        potential_contribution = current_salary - yearly_expenses
        total_contribution = potential_contribution + employer_contribution
            
        
        portfolio = total_contribution + (portfolio * market_rate) #TODO Doesn't include capital gains tax of 15%!!!!
        
        
        # ADDS INFO TO DATAFRAME
        data['Year'].append(starting_year + i)
        data['Age'].append(age)
        data['Salary'].append(current_salary)
        data['Expenses'].append(yearly_expenses)
        data['Contribution'].append(total_contribution)
        data['Portfolio'].append(max(portfolio,0))
        data["Portfolio in Today's Dollars"].append(max(0,portfolio * (inflation_discount ** i)))
    
    
    # CALCULATE RETIREMENT UTILIZATION
    for i in range(num_years,lifespan-starting_age):
        inflation_adjusted_expenses = (starting_expenses * (yearly_inflation_rate ** i) * (expenses_growth_rate ** num_years) * (expense_growth_retirement ** (i-num_years))) * expenses_in_retirement
            
        portfolio -= inflation_adjusted_expenses
        portfolio *= market_rate_in_retirement
        
        age = starting_age + + num_years + i
            
        data['Year'].append(starting_year + i)
        data['Age'].append(age)
        data['Salary'].append(0)
        data['Expenses'].append(inflation_adjusted_expenses)
        data['Contribution'].append(0)
        data['Portfolio'].append(max(portfolio,0))
        data["Portfolio in Today's Dollars"].append(max(0,portfolio * (inflation_discount ** i)))
    
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
