"""!
Vista que construye los controladores para las utilidades de la plataforma

@author Ing. Leonel P. Hernandez M. (leonelphm at gmail.com)
@author Ing. Luis Barrios (nikeven at gmail.com)
@copyright <a href='http://www.gnu.org/licenses/gpl-2.0.html'>GNU Public License versión 2 (GPLv2)</a>
@date 09-06-2017
@version 1.0.0
"""
import json
import random
import base64

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto import Random

from django.conf import settings
from django.core import signing
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView
from django.contrib import messages
from django.contrib.auth.mixins import (
    PermissionRequiredMixin, LoginRequiredMixin
)
from django.shortcuts import (
    redirect
)

from braces.views import GroupRequiredMixin

from users.models import TwoFactToken 

from .models import *
from .messages import MENSAJES_LOGIN


class LoginRequeridoPerAuth(LoginRequiredMixin, GroupRequiredMixin):
    """!
    Clase que construye el controlador para el login requerido, se sobreescribe el metodo dispatch

    @author Ing. Leonel Paolo Hernandez Macchiarulo  (leonelphm at gmail.com)
    @author Ing. Luis Barrios (nikeven at gmail.com)
    @copyright <a href='http://www.gnu.org/licenses/gpl-2.0.html'>GNU Public License versión 2 (GPLv2)</a>
    @date 09-06-2017
    @version 1.0.0
    """

    def dispatch(self, request, *args, **kwargs):
        """
        Envia una alerta al usuario que intenta acceder sin permisos para esta clase
        @return: Direcciona al login en caso de no poseer permisos, en caso contrario accede a la clase
        """
        if not request.user.is_authenticated:
            messages.warning(self.request, MENSAJES_LOGIN['LOGIN_REQUERIDO'])
            return self.handle_no_permission()
        valid_group = False
        grupos = request.user.groups.all()
        grupo = []
        if len(grupos) > 1:
            for g in grupos:
                grupo += str(g),
                if (str(g) in self.get_group_required()):
                    valid_group = True
        else:
            try:
                grupo = str(request.user.groups.get())
            except:
                return redirect('users:403error')
            if (grupo in self.get_group_required()):
                valid_group = True
        if not (valid_group):
            return redirect('users:403error')
        return super().dispatch(request, *args, **kwargs)


class StartView(LoginRequeridoPerAuth, TemplateView):
    """!
    Muestra el inicio de la plataforma

    @author Ing. Leonel Paolo Hernandez Macchiarulo  (leonelphm at gmail.com)
    @author Ing. Luis Barrios (nikeven at gmail.com)
    @copyright <a href='http://www.gnu.org/licenses/gpl-2.0.html'>GNU Public License versión 2 (GPLv2)</a>
    @date 09-01-2017
    @version 1.0.0
    @return: El template inicial de la plataforma
    """
    template_name = "utils_start.html"
    group_required = [u"Super Admin", u"Admin", u"Invitado"]


class TokenGenerator():
    """!
    Token Generator, based on Django signing

    @author Rodrigo Boet (rudmanmrrod@gmail.com)
    @author Ing. Luis Barrios (nikeven at gmail.com)
    @date 16-04-2017
    @version 1.0.0
    """

    def generate_token(self, user):
        """
        Generate token for user
        @param user Recives user objects
        @return token or False
        """
        try:
            token = signing.dumps(user.id)
            serial = random.randint(10000,99999)
            obj, created = TwoFactToken.objects.update_or_create(
                user=user,
                defaults={'token': token,'user': user,'serial':serial },
            )
            return str(serial)
        except:
            return False

    def check_token(self,user_id,token):
        """
        Check token for user
        @param user_id Recives user id
        @param token Recives token number
        @return Boolean
        """
        twofact = TwoFactToken.objects.filter(user_id=user_id)
        if(twofact):
            twofact = twofact.get()
            if(twofact.serial==int(token)):
                try:
                    signing.loads(twofact.token,max_age=350)
                    return True
                except:
                    return False
            else:
                return False
        else:
            return False

    def check_token_form(self, user_id, token):
        """
        Check token for user

        @param user_id Recives user id
        @param token Recives token number
        @return Boolean
        """
        token_val = TwoFactToken.objects.filter(user_id=user_id)
        if(token_val):
            token_val = token_val.get()
            try:
                signing.loads(token_val.token)
                return True
            except Exception as e:
                print(e)
                return False
        else:
            return False


class IpClient():
    """!
    Class to get the customers ip

    @author Ing. Leonel P. Hernandez M. (leonelphm@gmail.com)
    @author Ing. Luis Barrios (nikeven at gmail.com)
    @date 19-04-2017
    @version 1.0.0
    """

    def get_client_ip(self, request):
        """
        Gets the ip address that makes requestsCheck token for user

        @param request Recives request
        @return ip
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class DecodeEncodeChain():
    """

    """
    secret_key = settings.SECRET_KEY

    def encrypt(self, source, encode=True):
        if isinstance(self.secret_key, str):
            self.secret_key = str.encode(self.secret_key)
        if isinstance(source, str):
            source = str.encode(source)
        key = SHA256.new(self.secret_key).digest()  # use SHA-256 over our key to get a proper-sized AES key
        IV = Random.new().read(AES.block_size)  # generate IV
        encryptor = AES.new(key, AES.MODE_CBC, IV)
        padding = AES.block_size - len(source) % AES.block_size  # calculate needed padding
        source += bytes([padding]) * padding # Python 2.x: source += chr(padding) * padding
        data = IV + encryptor.encrypt(source)  # store the IV at the beginning and encrypt
        return base64.b64encode(data).decode("latin-1") if encode else data

    def decrypt(self, source, decode=True):
        if isinstance(self.secret_key, str):
            self.secret_key = str.encode(self.secret_key)
        if decode:
            source = base64.b64decode(source.encode("latin-1"))
        key = SHA256.new(self.secret_key).digest()  # use SHA-256 over our key to get a proper-sized AES key
        IV = source[:AES.block_size]  # extract the IV from the beginning
        decryptor = AES.new(key, AES.MODE_CBC, IV)
        data = decryptor.decrypt(source[AES.block_size:])  # decrypt
        padding = data[-1]  # pick the padding value from the end; Python 2.x: ord(data[-1])
        if data[-padding:] != bytes([padding]) * padding:  # Python 2.x: chr(padding) * padding
            raise ValueError("Invalid padding...")
        return data[:-padding]  # remove the padding