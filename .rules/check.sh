# Check authentication hook usage only when both rules exist.
USEAUTH_RULE="$RULES_DIR/useAuth.yml"
AUTHPROVIDER_RULE="$RULES_DIR/authProvider.yml"

if [[ -f "$USEAUTH_RULE" && -f "$AUTHPROVIDER_RULE" ]]; then
    echo "Checking authentication provider configuration..."

    USEAUTH_OUTPUT=$(ast-grep scan -r "$USEAUTH_RULE" 2>&1)
    USEAUTH_STATUS=$?

    AUTHPROVIDER_OUTPUT=$(ast-grep scan -r "$AUTHPROVIDER_RULE" 2>&1)
    AUTHPROVIDER_STATUS=$?

    if [[ $USEAUTH_STATUS -ne 0 || $AUTHPROVIDER_STATUS -ne 0 ]]; then
        echo "Authentication rule execution failed."
        EXIT_CODE=1
    elif [[ -n "$USEAUTH_OUTPUT" && -z "$AUTHPROVIDER_OUTPUT" ]]; then
        echo "Potential issue: useAuth may be used without AuthProvider."
        EXIT_CODE=1
    fi
else
    echo "Skipping authentication provider check: rules not found."
fi