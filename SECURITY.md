# Security Considerations

## API Keys and Secrets

- All API keys are loaded from environment variables, never hardcoded
- `.env` files are excluded via `.gitignore`
- Users must provide their own API keys via environment variables

## Error Handling

- Full tracebacks are only exposed when `DEBUG=true` environment variable is set
- In production (default), only error messages are returned to prevent information leakage
- Internal errors are logged server-side for debugging

## CORS Configuration

- Currently configured with `allow_origins=["*"]` for development
- **For production**: Update CORS configuration in `src/api/main.py` to specify allowed origins
- Consider restricting to specific domains that need access

## Input Validation

- URLs are validated using Pydantic's `HttpUrl` type
- Domain names are validated to match existing blueprint files
- All input is validated before processing

## Rate Limiting

- **Not currently implemented** - Consider adding rate limiting for production use
- Recommended: Use FastAPI middleware or reverse proxy (nginx) for rate limiting

## Security Best Practices

1. **Never commit `.env` files** - They are excluded via `.gitignore`
2. **Use strong API keys** - Rotate keys regularly
3. **Monitor usage** - Watch for unusual patterns that might indicate abuse
4. **Keep dependencies updated** - Regularly update packages for security patches
5. **Use HTTPS in production** - Never expose the API over HTTP

## Reporting Security Issues

If you discover a security vulnerability, please report it responsibly rather than opening a public issue.

