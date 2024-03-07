# reshapelab.github.io
Project Page

Steps to deploy to Github Pages

To recommit new changes and push up to the remote repository:

1. On remote repository delete the "gh-pages" branch. 

2. In you local repository run this command: npm run build (1:56)

3. git add dist -f (2:05)

4. git commit -m [your commit message here] (2:17)

5. git subtree push --prefix dist origin gh-pages (2:20)