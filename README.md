# SDDC Common Dependencies module for Sublime Text

![Version 0.6.5](https://img.shields.io/badge/version-v0.6.5-blue.svg)

## How to use *sddc_common* as a dependency

In order to tell Package Control that you are using the *sddc_common* module
in your ST package, create a `dependencies.json` file in your package root
with the following contents:

```js
{
   "*": {
      "*": [
         "sddc_common"
      ]
   }
}
```

If the file exists already, add `"sddc_common"` to the every dependency list.

Then run the **Package Control: Satisfy Dependencies** command to make Package Control
install the module for you locally (if you don't have it already).

After all this you can use `import sddc_common` in any of your Python plugins.

See also:
[Documentation on Dependencies](https://packagecontrol.io/docs/dependencies)

