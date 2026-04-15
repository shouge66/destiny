"""
URL configuration for gift_tracker project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path


def api_root(request):
        return HttpResponse(
                """
                <html>
                    <head><title>gift_tracker API</title></head>
                    <body style='font-family: sans-serif; padding: 24px;'>
                        <h1>gift_tracker API</h1>
                        <p>Service is running.</p>
                        <ul>
                            <li><a href='/api/health/'>Health Check</a></li>
                            <li><a href='/admin/'>Admin</a></li>
                        </ul>
                    </body>
                </html>
                """
        )

urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]
