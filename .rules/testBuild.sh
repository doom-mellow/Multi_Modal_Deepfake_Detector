
#!/usr/bin/env bash

set -u

BUILD_DIR="node_modules/.deepshield-test-build"

# Remove any previous test build.
rm -rf "$BUILD_DIR"

# Run a production build without minification.
if npx vite build \
    --minify false \
    --logLevel error \
    --outDir "$BUILD_DIR" \
    --emptyOutDir; then

    echo "Build check passed."

    # Remove temporary build output.
    rm -rf "$BUILD_DIR"
    exit 0
else
    EXIT_CODE=$?

    echo "Build check failed."
    echo "Please review the errors above."

    # Remove incomplete build output.
    rm -rf "$BUILD_DIR"
    exit "$EXIT_CODE"
fi
