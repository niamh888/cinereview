print("Hello World!")
print("This is a simple Python script.")
print("You can add more functionality here as needed.") 

# Example of a function
def greet(name):
    return f"Hello, {name}!"    
# Example usage of the function
name = "Alice"  
greeting = greet(name)
print(greeting)
# Example of a loop
for i in range(5):
    print(f"Iteration {i + 1}")
# Example of a conditional statement
number = 10
if number > 5:
    print(f"{number} is greater than 5.")
else:
    print(f"{number} is not greater than 5.")
# Example of a list and a loop to iterate through it
fruits = ["apple", "banana", "cherry"]
for fruit in fruits:
    print(f"I like {fruit}.")
# Example of a dictionary
person = {
    "name": "Bob",
    "age": 30,
    "city": "New York"
}
print(f"{person['name']} is {person['age']} years old and lives in {person['city']}.")

    