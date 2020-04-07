# dlmt README

> Experimental format for storing monochrome vectorial images

## Features

This media format, mostly for monochrome images is an intermediate format, which:
* is scalable, and use fractions to represent shapes.
* accepts different coordinate systems.
* is simple enough to be converted to other formats easily.
* can be converted to SVG, PNG, JPG.
* facilitates the creation of stencils.
* avoid support of special effects
* makes it easy to export a part of the image.
* is organized around the concept of scalable brushes
* allows to add tags the the brushstrokes

## Requirements

If you intend to convert this format to a more standard one (svg, png, jpg), you will need to install Python 3.7.

## Extension Settings

Include if your extension adds any VS Code settings through the `contributes.configuration` extension point.

For example:

This extension contributes the following settings:

* `myExtension.enable`: enable/disable this extension
* `myExtension.thing`: set to `blah` to do something

## Known Issues

Calling out known issues can help limit users opening duplicate issues against your extension.

## Release Notes

Users appreciate release notes as you update your extension.

### 0.5.0

Initial release.

