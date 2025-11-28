#!/bin/bash

if [ "$1" = "-s" ]; then
  echo "Starting Hugo server in preview mode..."
  hugo server -D
else
  $1

  # Add front matter to posts before building
  echo "Adding front matter to posts..."
  python3 add_frontmatter.py
  
  # Clean and build
  rm -rf ./resources
  rm -rf ./public
  hugo -D -d docs
  
  # Restore original files (remove front matter)
  echo "Restoring original files..."
  git restore content/posts
fi