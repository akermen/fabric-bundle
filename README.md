# Git Bundle Deployment with Fabric

Fabric methods to create [Git bundles](https://git-scm.com/docs/git-bundle) inlcuding direct [submodules](https://www.git-scm.com/book/en/v2/Git-Tools-Submodules) to be used for offline deployment. Submodule bundle support is adapted from [git subundle](https://github.com/xeyownt/git-subundle). This project utilize [Python](https://www.python.org) and [Fabric](http://www.fabfile.org) to make bundle support practicial especially for deployment tasks.

### Installation
```bash
make install
```

### Usage

To create bundle:
```bash
.virtualenv/bin/fab mode_local git_bundle:Projects/source_repository,Projects/source.bundle
```

To deploy bundle to local for testing:
```bash
.virtualenv/bin/fab mode_local git_unbundle:/temp/source.bundle,/temp/target/
```

To deploy bundle to remote host:
```bash
.virtualenv/bin/fab --hosts host1 mode_remote git_unbundle:/temp/source.bundle,/var/www/target_repository/
```

Bundle and deploy with single command:
```bash
.virtualenv/bin/fab --hosts host1 deploy_bundle:Projects/source_repository,/var/www/target_repository/
```

## Dependencies
- [Fabric](http://www.fabfile.org)
- [cuisine](https://github.com/sebastien/cuisine)
- [Python 2.7](https://www.python.org)

## Notes
- [Python 3](https://www.python.org) is not supported due to [cuisine](https://github.com/sebastien/cuisine) which appears to be not ready for [Python 3](https://www.python.org) yet: [https://github.com/sebastien/cuisine/issues/133](https://github.com/sebastien/cuisine/issues/133).