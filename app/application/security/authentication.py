from typing import Protocol

from app.application.security.identity import IdentityContext


class AuthenticationProvider(Protocol):
    """
    Authentication boundary for ELR.

    Concrete authentication mechanisms such as OAuth2, OpenID Connect,
    or an enterprise identity provider are intentionally outside the
    initial implementation scope.
    """

    def authenticate(
        self,
        credentials: object,
    ) -> IdentityContext:
        """
        Authenticate the supplied credentials and return an
        authenticated IdentityContext.

        Implementations must raise an authentication-related
        application error when the identity cannot be established.
        """
        ...
