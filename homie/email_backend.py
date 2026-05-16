import ssl
from django.core.mail.backends.smtp import EmailBackend as SmtpEmailBackend

class UnverifiedEmailBackend(SmtpEmailBackend):
    """
    Un backend de correo que ignora los errores de certificado SSL.
    Útil para entornos locales o redes controladas por antivirus/firewalls
    estrictos que interceptan el tráfico HTTPS/TLS.
    """
    @property
    def ssl_context(self):
        # Crear un contexto SSL que NO verifique certificados
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context
