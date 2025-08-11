# handlebars-helpers-v2

> Essential Handlebars helpers in TypeScript. A modernized collection of 8 core helper categories with TypeScript support and ESM compatibility.

## Features

- ✅ **TypeScript Native** - Written in TypeScript with full type support
- ✅ **ESM & CommonJS** - Supports both module systems
- ✅ **Security First** - No security vulnerabilities, minimal dependencies
- ✅ **Performance Focused** - Native implementations instead of heavy dependencies
- ✅ **Well Tested** - 315+ comprehensive tests covering all helpers
- ✅ **Modern Tooling** - Built with pnpm, compiled with TypeScript

## Install

Install with npm:

```sh
npm install handlebars-helpers-v2
```

Install with pnpm:

```sh
pnpm add handlebars-helpers-v2
```

Install with yarn:

```sh
yarn add handlebars-helpers-v2
```

## Usage

### ES Modules (Recommended)

```js
import { array, string, math } from 'handlebars-helpers-v2';
import Handlebars from 'handlebars';

// Register specific helper categories
Object.keys(array).forEach(name => {
  Handlebars.registerHelper(name, array[name]);
});

Object.keys(string).forEach(name => {
  Handlebars.registerHelper(name, string[name]);
});
```

### Using Default Export

```js
import handlebarsHelpers from 'handlebars-helpers-v2';
import Handlebars from 'handlebars';

// Register all helpers automatically
handlebarsHelpers({ handlebars: Handlebars });

// Or get specific collections
const arrayHelpers = handlebarsHelpers(['array']);
const stringAndMathHelpers = handlebarsHelpers(['string', 'math']);

// Or get all helpers as an object
const allHelpers = handlebarsHelpers();
```

### Using Getter Functions

```js
import handlebarsHelpers from 'handlebars-helpers-v2';
import Handlebars from 'handlebars';

// Auto-register specific category
handlebarsHelpers.array({ handlebars: Handlebars });
handlebarsHelpers.string({ handlebars: Handlebars });

// Or just get the helpers without registering
const arrayHelpers = handlebarsHelpers.array();
const stringHelpers = handlebarsHelpers.string();
```

### CommonJS

```js
const { array, string, math } = require('handlebars-helpers-v2');
const Handlebars = require('handlebars');

// Register specific helper categories
Object.keys(array).forEach(name => {
  Handlebars.registerHelper(name, array[name]);
});

Object.keys(string).forEach(name => {
  Handlebars.registerHelper(name, string[name]);
});
```

### CommonJS with Default Export

```js
const handlebarsHelpers = require('handlebars-helpers-v2').default;
const Handlebars = require('handlebars');

// Register all helpers automatically
handlebarsHelpers({ handlebars: Handlebars });

// Or use getter functions
handlebarsHelpers.array({ handlebars: Handlebars });
handlebarsHelpers.string({ handlebars: Handlebars });
```

### TypeScript

```ts
import { array, string, math } from 'handlebars-helpers-v2';
import handlebarsHelpers from 'handlebars-helpers-v2';
import * as Handlebars from 'handlebars';

// Import named exports with full type support
Object.entries(array).forEach(([name, helper]) => {
  Handlebars.registerHelper(name, helper);
});

// Or use default export with auto-registration
handlebarsHelpers({ handlebars: Handlebars });

// Or use getter functions with types
const arrayHelpers = handlebarsHelpers.array();
const stringHelpers = handlebarsHelpers.string();
```

## Helper Categories

This package includes **8 essential helper categories**:

| Category | Helpers | Description |
|----------|---------|-------------|
| **[array](#array)** | 25+ | Array manipulation and iteration |
| **[collection](#collection)** | 2+ | Object and collection utilities |
| **[comparison](#comparison)** | 15+ | Logical comparisons and conditionals |
| **[date](#date)** | 5+ | Date formatting and manipulation |
| **[math](#math)** | 10+ | Mathematical operations |
| **[number](#number)** | 10+ | Number formatting and utilities |
| **[string](#string)** | 30+ | String manipulation and formatting |
| **[url](#url)** | 5+ | URL parsing and manipulation |

## Examples

### Array Helpers

```handlebars
<!-- Array manipulation -->
{{#each (after items 2)}}
  <li>{{this}}</li>
{{/each}}

<!-- Array filtering -->
{{#filter items "age" 21}}
  <p>{{name}} is old enough</p>
{{/filter}}

<!-- Array length check -->
{{#lengthEqual items 5}}
  <p>Exactly 5 items!</p>
{{/lengthEqual}}
```

### String Helpers

```handlebars
<!-- String formatting -->
<h1>{{titleize "hello world"}}</h1>
<!-- Output: <h1>Hello World</h1> -->

<!-- String manipulation -->
<p>{{truncate description 100}}</p>
<span>{{capitalize name}}</span>

<!-- Case conversion -->
{{pascalcase "foo-bar-baz"}} <!-- FooBarBaz -->
{{camelcase "foo bar baz"}}   <!-- fooBarBaz -->
{{snakecase "foo bar baz"}}   <!-- foo_bar_baz -->
```

### Math Helpers

```handlebars
<!-- Mathematical operations -->
<p>Total: ${{add price tax}}</p>
<p>Average: {{avg scores}}</p>
<p>{{#gt score 85}}Grade: A{{else}}Grade: B{{/gt}}</p>

<!-- Number formatting -->
<span>{{toFixed percentage 2}}%</span>
```

### Comparison Helpers

```handlebars
<!-- Logical comparisons -->
{{#and user.active user.verified}}
  <span class="verified">✓ Active & Verified</span>
{{/and}}

<!-- Value checking -->
{{#isFalsey value}}
  <p>Value is falsey (including 'nope', 'nil', etc.)</p>
{{/isFalsey}}

<!-- Contains checking -->
{{#contains tags "featured"}}
  <span class="featured">⭐ Featured</span>
{{/contains}}
```

### Date Helpers

```handlebars
<!-- Date formatting -->
<time>{{formatDate createdAt "YYYY-MM-DD"}}</time>
<span>{{timeago publishedAt}}</span>

<!-- Date comparisons -->
{{#isAfter endDate startDate}}
  <p>Event is valid</p>
{{/isAfter}}
```

### URL Helpers

```handlebars
<!-- URL manipulation -->
<a href="{{stripProtocol website}}">{{domain}}</a>

<!-- URL parsing -->
{{#with (urlParse "https://example.com/path?q=search")}}
  <p>Host: {{hostname}}</p>
  <p>Path: {{pathname}}</p>
  <p>Query: {{query}}</p>
{{/with}}
```

## API Reference

### Helper Categories

Each category is exported as a separate object:

```js
import { 
  array,      // Array helpers
  collection, // Collection helpers  
  comparison, // Comparison helpers
  date,       // Date helpers
  math,       // Math helpers
  number,     // Number helpers
  string,     // String helpers
  url         // URL helpers
} from 'handlebars-helpers-v2';
```

### Individual Helpers

You can also import individual helpers:

```js
// Array helpers
const { first, last, join, sort } = array;

// String helpers  
const { capitalize, truncate, replace } = string;

// Math helpers
const { add, subtract, multiply, divide } = math;
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b my-new-feature`
3. Make your changes and add tests
4. Run tests: `pnpm test`
5. Build: `pnpm build`
6. Commit: `git commit -am 'Add some feature'`
7. Push: `git push origin my-new-feature`
8. Submit a pull request

## Development

```sh
# Install dependencies
pnpm install

# Run tests
pnpm test

# Build TypeScript
pnpm build

# Run linting
pnpm lint

# Run type checking
pnpm typecheck
```

## Version History

### v1.0.0 (TypeScript Rewrite)
- Complete TypeScript rewrite
- Modern ESM/CommonJS dual package
- Reduced from 130+ to 80+ essential helpers
- Zero security vulnerabilities  
- Native implementations replace heavy dependencies
- 315+ comprehensive tests
- Full type safety

## License

Released under the [MIT License](LICENSE).

## Credits

This project is a TypeScript rewrite and modernization of the original [handlebars-helpers](https://github.com/helpers/handlebars-helpers) by [Jon Schlinkert](https://github.com/jonschlinkert) and contributors. The original project provided the foundation and inspiration for this modern implementation.

**Original Repository**: https://github.com/helpers/handlebars-helpers  
**Original Author**: Jon Schlinkert  
**License**: MIT (maintained)

## Related

- [handlebars](https://handlebarsjs.com/) - The semantic template language
- [template-helpers](https://github.com/jonschlinkert/template-helpers) - Generic template helpers
- [handlebars-helpers](https://github.com/helpers/handlebars-helpers) - Original handlebars-helpers project

---

**Modernized with ❤️ for the TypeScript era**