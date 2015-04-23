# repo-gif

Generate a gif of the contents of the files tracked by a repository,
one frame per commit. Meant to be a neato way to look at a project's
changes over time from a birds-eye view.

This is currently under heavy development, and takes a silly amount of
time. And it's ugly. It'll get better, I promise.

Usage: `repo_gif /path/to/repo /path/to/output.gif`

Depends on:
  + the packages in requirements.txt
  + imagemagick's `convert` command because I can't for the life of me
    get pillow to generate a gif.
