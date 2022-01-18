# Adobe Admin Console Management

This repository will document the Adobe Admin Console wrapper.
This is based on the same architecture that the different python library are built for the Adobe API (aanalytics2, launchpy, aepp, etc..) 
## Installation

You can install the module directly from a pypi command:

```shell
pip install adobeadminconsole
```

The version of the wrapper can be seen by the following command (once loaded):

```python
import adobeadminconsole as admin
admin.__version__

```

**Consider upgrading regulary**

```shell
pip install adobeadminconsole --upgrade
```

## Getting Started

In order to get started, I have compile a guide to help you initialize this module and what is required.
You can find this documentation [here](./docs/getting-started.md)

## Admin Console docs

At the moment the current wrapper is containing the following sub modules:

* [Main](./docs/main.md)

## Releases

Release notes are accessible [here](./docs/releases.md).
