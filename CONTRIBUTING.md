# Contributing to Electroduction

First off, thank you for considering contributing to Electroduction! This document provides guidelines and instructions for contributing to this project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Process](#development-process)
- [Style Guidelines](#style-guidelines)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all. Please be respectful and constructive in your interactions.

### Our Standards

**Positive behavior includes:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards others

**Unacceptable behavior includes:**
- Harassment of any kind
- Trolling, insulting/derogatory comments
- Publishing others' private information
- Other conduct which could reasonably be considered inappropriate

---

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates.

**When reporting a bug, include:**
- Clear, descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Screenshots (if applicable)
- Browser and OS information
- Code samples (if relevant)

**Example Bug Report:**

```markdown
**Title:** Cart total not updating when removing items

**Steps to Reproduce:**
1. Add items to cart
2. Click "Remove" on any item
3. Observe the total price

**Expected:** Total should recalculate
**Actual:** Total remains unchanged

**Browser:** Chrome 118
**OS:** Windows 11
```

### Suggesting Enhancements

We welcome enhancement suggestions! Please include:

- Clear description of the enhancement
- Rationale (why it would be useful)
- Examples or mockups (if applicable)
- Implementation ideas (optional)

**Example Enhancement Suggestion:**

```markdown
**Enhancement:** Add dark mode toggle to all websites

**Rationale:** Many users prefer dark mode, especially for extended use

**Implementation:**
- Add toggle button in header
- Use CSS variables for colors
- Save preference to localStorage
- Respect system preference by default
```

### Contributing Code

**Types of contributions we're looking for:**

✅ **Bug Fixes**: Fixing broken functionality
✅ **Feature Enhancements**: Improving existing features
✅ **New Features**: Adding valuable new capabilities
✅ **Documentation**: Improving guides and comments
✅ **Performance**: Optimizing code efficiency
✅ **Accessibility**: Improving ARIA labels, keyboard navigation
✅ **Tests**: Adding test coverage
✅ **Design**: UI/UX improvements

**Types of contributions we're generally not looking for:**

❌ Framework rewrites (this project intentionally uses vanilla JS)
❌ Large external dependencies
❌ Changes that don't align with project philosophy
❌ Style-only changes without functional improvement

---

## Development Process

### 1. Fork the Repository

```bash
# Fork via GitHub UI, then clone your fork:
git clone https://github.com/YOUR_USERNAME/Electroduction.git
cd Electroduction
```

### 2. Create a Branch

```bash
# Create a descriptive branch name
git checkout -b feature/add-dark-mode
git checkout -b fix/cart-total-bug
git checkout -b docs/improve-readme
```

**Branch naming conventions:**
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Adding tests
- `perf/description` - Performance improvements

### 3. Make Your Changes

**Before you start coding:**

1. Read relevant documentation
2. Understand the existing code structure
3. Follow the established patterns
4. Keep changes focused and atomic

**While coding:**

1. Write clean, readable code
2. Add comments for complex logic
3. Follow the style guidelines below
4. Test your changes thoroughly

### 4. Test Your Changes

**Manual Testing Checklist:**

```
□ Open the file in multiple browsers (Chrome, Firefox, Safari)
□ Test on different screen sizes (mobile, tablet, desktop)
□ Verify all interactive features work
□ Check console for errors
□ Test edge cases
□ Verify accessibility (keyboard navigation, screen readers)
```

**Browser Testing:**
- Chrome/Edge (latest 2 versions)
- Firefox (latest 2 versions)
- Safari (latest version)

### 5. Commit Your Changes

```bash
git add .
git commit -m "Fix: Correct cart total calculation when removing items"
```

See [Commit Guidelines](#commit-guidelines) below for details.

### 6. Push to Your Fork

```bash
git push origin feature/add-dark-mode
```

### 7. Create Pull Request

Go to GitHub and create a Pull Request from your fork to the main repository.

---

## Style Guidelines

### JavaScript Style

**General Principles:**
- Use modern ES6+ syntax
- Prefer `const` over `let`, never use `var`
- Use descriptive variable and function names
- Keep functions small and focused
- Add comments for complex logic

**Code Examples:**

```javascript
// ✅ Good: Descriptive names, const, arrow functions
const calculateCartTotal = (cartItems) => {
    return cartItems.reduce((sum, item) => sum + item.price * item.quantity, 0);
};

// ❌ Bad: Unclear names, var, old syntax
var calc = function(items) {
    var total = 0;
    for (var i = 0; i < items.length; i++) {
        total = total + items[i].price * items[i].quantity;
    }
    return total;
};
```

**Naming Conventions:**

```javascript
// Variables and functions: camelCase
const productList = [];
function renderProducts() {}

// Constants: UPPER_SNAKE_CASE
const MAX_CART_ITEMS = 100;
const API_URL = 'https://api.example.com';

// Classes: PascalCase (if used)
class ProductCatalog {}
```

**Function Documentation:**

```javascript
/**
 * Adds a product to the shopping cart
 * Handles duplicate items by incrementing quantity
 * @param {number} productId - ID of the product to add
 * @returns {boolean} - True if added successfully
 */
function addToCart(productId) {
    // Implementation
}
```

### HTML Style

```html
<!-- ✅ Good: Semantic, properly indented, attributes organized -->
<article class="product-card" data-id="123">
    <h2 class="product-title">Product Name</h2>
    <p class="product-description">Description text</p>
    <button
        class="btn btn-primary"
        onclick="addToCart(123)"
        aria-label="Add Product Name to cart"
    >
        Add to Cart
    </button>
</article>

<!-- ❌ Bad: Non-semantic, poor indentation, missing accessibility -->
<div class="card">
<div class="title">Product Name</div>
<div>Description text</div>
<div onclick="addToCart(123)">Add to Cart</div>
</div>
```

### CSS Style

```css
/* ✅ Good: Organized, well-commented, consistent */

/* ===================
   Product Card Styles
   =================== */

.product-card {
    /* Layout */
    display: flex;
    flex-direction: column;
    padding: 1.5rem;

    /* Visual */
    background: white;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);

    /* Interaction */
    transition: transform 0.3s ease;
}

.product-card:hover {
    transform: translateY(-5px);
}

/* ❌ Bad: Unclear, no organization, inconsistent spacing */
.product-card{background:white;padding:1.5rem;border-radius:10px;}
.product-card:hover{transform:translateY(-5px);}
```

**CSS Organization:**

```css
/* File structure */

/* 1. CSS Reset */
* { margin: 0; padding: 0; box-sizing: border-box; }

/* 2. CSS Variables */
:root {
    --primary-color: #667eea;
    --secondary-color: #764ba2;
}

/* 3. Global Styles */
body { font-family: sans-serif; }

/* 4. Layout Components */
.header { }
.sidebar { }
.main { }

/* 5. UI Components */
.button { }
.card { }

/* 6. Utilities */
.text-center { text-align: center; }
.hidden { display: none; }

/* 7. Media Queries */
@media (max-width: 768px) { }
```

---

## Commit Guidelines

### Commit Message Format

```
<type>: <subject>

<body (optional)>

<footer (optional)>
```

**Types:**

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `style:` Code style (formatting, semicolons, etc.)
- `refactor:` Code refactoring
- `perf:` Performance improvement
- `test:` Adding tests
- `chore:` Maintenance tasks

**Examples:**

```bash
# Good commit messages
git commit -m "feat: Add dark mode toggle to all websites"
git commit -m "fix: Correct cart total calculation when removing items"
git commit -m "docs: Add API documentation to README"
git commit -m "perf: Optimize product rendering with document fragments"

# Bad commit messages
git commit -m "fixed stuff"
git commit -m "updates"
git commit -m "WIP"
```

**Detailed Commit Example:**

```bash
git commit -m "feat: Add search functionality to recipe website

- Implement real-time search across recipe titles and descriptions
- Add debouncing to prevent excessive filtering
- Update UI to show 'no results' message when appropriate
- Add keyboard shortcut (Ctrl/Cmd+K) to focus search

Closes #42"
```

### Commit Best Practices

✅ **Do:**
- Write clear, descriptive commit messages
- Make atomic commits (one logical change per commit)
- Commit working code
- Reference issue numbers when applicable

❌ **Don't:**
- Commit broken code
- Bundle unrelated changes
- Use vague messages like "fix" or "update"
- Commit commented-out code or debug statements

---

## Pull Request Process

### Before Submitting

**Checklist:**

```
□ Code follows style guidelines
□ All tests pass
□ Tested in multiple browsers
□ Documentation updated (if needed)
□ Commit messages follow guidelines
□ Branch is up to date with main
□ No merge conflicts
```

### PR Title Format

Similar to commit messages:

```
feat: Add dark mode toggle
fix: Correct cart calculation bug
docs: Improve deployment guide
```

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe how you tested the changes

## Screenshots (if applicable)
Add screenshots here

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-reviewed code
- [ ] Commented complex code
- [ ] Documentation updated
- [ ] No new warnings
- [ ] Tested in multiple browsers

## Related Issues
Closes #123
```

### Review Process

1. **Automated Checks**: Must pass (when implemented)
2. **Code Review**: At least one approval required
3. **Testing**: Reviewer will test functionality
4. **Feedback**: Address any requested changes
5. **Merge**: Approved PRs will be merged by maintainers

### After Your PR is Merged

1. Delete your branch (optional)
2. Pull the latest changes
3. Celebrate! 🎉

```bash
git checkout main
git pull origin main
git branch -d feature/your-feature
```

---

## Development Philosophy

### Project Principles

1. **Vanilla First**: Avoid external dependencies
2. **Simplicity**: Simple solutions over clever complexity
3. **Performance**: Optimize for speed and efficiency
4. **Accessibility**: Make features usable for everyone
5. **Education**: Code should teach as well as function
6. **Quality**: Better to do fewer things well

### Code Review Focus

When reviewing code, we look for:

✅ **Functionality**: Does it work as intended?
✅ **Readability**: Is the code easy to understand?
✅ **Performance**: Is it efficient?
✅ **Security**: Are there any vulnerabilities?
✅ **Accessibility**: Can everyone use it?
✅ **Consistency**: Does it match existing patterns?
✅ **Documentation**: Is it well-commented?

---

## Getting Help

### Resources

- **Documentation**: Read the [README](README.md) and [ARCHITECTURE](ARCHITECTURE.md)
- **Issues**: Search [existing issues](https://github.com/Electroduction/Electroduction/issues)
- **Discussions**: Check [GitHub Discussions](https://github.com/Electroduction/Electroduction/discussions)

### Questions?

- Open a GitHub Discussion for general questions
- Open an Issue for specific bugs or feature requests
- Tag your issue with `question` label

---

## Recognition

Contributors will be recognized in:

- README contributors section
- Release notes
- GitHub contributors graph

---

## Final Notes

### Remember

- Be patient and kind
- Ask questions when unsure
- Learn from feedback
- Have fun coding!

### Philosophy

> "Quality over quantity. We prefer one well-implemented feature over ten rushed ones."

---

Thank you for contributing to Electroduction! Your efforts help make this project better for everyone. 🙏

**Happy Coding!** 🚀
