# 🧪 CodeMind Editor Test Content

Use these code snippets to test all editor features!

---

## 🎓 BEGINNER MODE TESTS

### Test 1: Simple Function (Beginner Mode)
**Enable Beginner Mode first, then paste this:**

```python
def add(a, b):
    return a + b
```

**Expected:** Should show 2-3 style options (Concise, Descriptive, Professional)

---

### Test 2: Basic Calculator Function
```python
def calc(x, y):
    if x > y:
        return x + y
    else:
        return x - y
```

**Expected:** Multiple style options with different error handling and documentation styles

---

### Test 3: Simple List Operation
```python
def get_max(numbers):
    max_num = numbers[0]
    for n in numbers:
        if n > max_num:
            max_num = n
    return max_num
```

**Expected:** Options showing different naming conventions and documentation styles

---

## 🤖 REGULAR MODE TESTS (Disable Beginner Mode)

### Test 4: Function with Type Hints
```python
def calculate_factorial(n: int) -> int:
    if n <= 1:
        return 1
    return n * calculate_factorial(n - 1)
```

**Expected:** AI suggestion matching your style profile

---

### Test 5: Function with Error Handling
```python
def divide_numbers(a, b):
    result = a / b
    return result
```

**Expected:** Suggestion to add error handling (try/except) if your profile prefers it

---

### Test 6: Undocumented Function
```python
def process_data(data):
    cleaned = []
    for item in data:
        if item and item.strip():
            cleaned.append(item.strip().lower())
    return cleaned
```

**Expected:** Suggestion to add docstring if your profile prefers documentation

---

## 🌐 MULTI-LANGUAGE TESTS

### Test 7: JavaScript Function
**Change language to JavaScript, then paste:**

```javascript
function findMax(arr) {
    let max = arr[0];
    for (let i = 1; i < arr.length; i++) {
        if (arr[i] > max) {
            max = arr[i];
        }
    }
    return max;
}
```

**Expected:** AI suggestions matching JavaScript patterns

---

### Test 8: TypeScript Function
**Change language to TypeScript:**

```typescript
function greet(name: string): string {
    return "Hello, " + name;
}
```

**Expected:** TypeScript-specific suggestions

---

### Test 9: Java Method
**Change language to Java:**

```java
public int sum(int a, int b) {
    return a + b;
}
```

**Expected:** Java-style suggestions

---

## 🚀 CODE GENERATION TESTS

### Test 10: Simple Request
**In the code generation input, type:**
```
Create a function to check if a number is prime
```

**Expected:** Generated code matching your style profile

---

### Test 11: Web App Template
**Click "🌐 Web App" template button, then type:**
```
Create a todo list app
```

**Expected:** Multiple files generated (HTML, CSS, JavaScript)

---

### Test 12: Flask App Template
**Click "🐍 Flask App" template button, then type:**
```
Create a simple blog API
```

**Expected:** Multiple files (app.py, templates, static files)

---

### Test 13: REST API Template
**Click "🔌 REST API" template button, then type:**
```
Create a user management API
```

**Expected:** Multiple files with endpoints, models, etc.

---

### Test 14: Custom Tech Stack
**Type in tech stack input:**
```
React + Node.js + MongoDB
```

**Then in request input:**
```
Create a user authentication system
```

**Expected:** Code generated using specified tech stack

---

## 📝 COMPLEX CODE TESTS

### Test 15: Class Definition
```python
class Calculator:
    def __init__(self):
        self.result = 0
    
    def add(self, x):
        self.result += x
        return self.result
    
    def subtract(self, x):
        self.result -= x
        return self.result
```

**Expected:** Suggestions for better class structure, docstrings, type hints

---

### Test 16: Function with Multiple Parameters
```python
def process_user_data(name, age, email, is_active):
    user = {
        'name': name,
        'age': age,
        'email': email,
        'active': is_active
    }
    return user
```

**Expected:** Suggestions for better parameter handling, validation, type hints

---

### Test 17: Function with List Comprehension
```python
def filter_even(numbers):
    evens = []
    for n in numbers:
        if n % 2 == 0:
            evens.append(n)
    return evens
```

**Expected:** Suggestion to use list comprehension if your style prefers it

---

## 🔄 FEEDBACK TESTS

### Test 18: Accept/Reject Suggestions
1. Write any function
2. Wait for AI suggestion
3. Click "✅ Accept" - should learn from acceptance
4. Write another function
5. Click "❌ Reject" - should learn from rejection

**Expected:** Profile updates based on accept/reject actions

---

## 🎯 BEGINNER MODE INTERACTION TESTS

### Test 19: Multiple Style Choices
1. Enable Beginner Mode
2. Write: `def multiply(a, b): return a * b`
3. See 3 style options
4. Click "Descriptive & Clear" option
5. Write another function
6. See options again - should be more aligned to your previous choice

**Expected:** CodeMind learns from your style choices

---

### Test 20: Incremental Learning
1. Enable Beginner Mode
2. Write 5 different simple functions
3. Choose different style options each time
4. After 5-10 interactions, check if suggestions align with your choices

**Expected:** After 10 interactions, CodeMind knows your style preferences

---

## 📊 MULTI-FILE GENERATION TESTS

### Test 21: Complete Project
**Click "🌐 Web App" template, then type:**
```
Create a weather dashboard with API integration
```

**Expected:** Multiple files:
- `index.html`
- `style.css`
- `app.js`
- Possibly `config.js`

**Then:**
- Click "✅ Accept All" - all files should be applied to editor
- Or click individual "✅ Accept" buttons for each file

---

### Test 22: Flask Project
**Click "🐍 Flask App" template, then type:**
```
Create a simple e-commerce site
```

**Expected:** Multiple files:
- `app.py`
- `templates/index.html`
- `static/css/style.css`
- `requirements.txt`

---

## 🧪 EDGE CASE TESTS

### Test 23: Very Short Code
```python
x = 5
```

**Expected:** Should not trigger suggestions (too short)

---

### Test 24: Code with Comments
```python
# This function adds two numbers
def add(a, b):
    return a + b  # Return the sum
```

**Expected:** Suggestions respecting or improving comment style

---

### Test 25: Code with Errors
```python
def broken_function(x):
    result = x / 0
    return result
```

**Expected:** Suggestions to fix errors and add error handling

---

## 📋 QUICK TEST CHECKLIST

- [ ] Beginner Mode: Simple function shows multiple options
- [ ] Beginner Mode: Selecting option applies code
- [ ] Beginner Mode: Learning from choices works
- [ ] Regular Mode: AI suggestions appear after 2 seconds
- [ ] Regular Mode: Accept/Reject updates profile
- [ ] Code Generation: Single file generation works
- [ ] Code Generation: Multi-file generation works
- [ ] Code Generation: Template buttons work
- [ ] Code Generation: Custom tech stack works
- [ ] Multi-file: Accept All button works
- [ ] Multi-file: Individual Accept buttons work
- [ ] Language Selector: Changes editor language
- [ ] Language Selector: Suggestions match language

---

## 💡 TIPS FOR TESTING

1. **Start with Beginner Mode** - Test the learning mechanism first
2. **Test with different code lengths** - Short vs long functions
3. **Test with different languages** - Python, JavaScript, TypeScript, Java
4. **Test template buttons** - Each should generate appropriate multi-file projects
5. **Test feedback loop** - Accept/reject suggestions and see if profile updates
6. **Test incremental learning** - Make 10+ choices in Beginner Mode
7. **Test multi-file acceptance** - Accept all vs individual files

---

**Happy Testing! 🚀**

