# Checklist - Preparar Datos para FASE 14
## ¿Qué información necesita el sistema?

---

## 📋 1. LISTA DE CLIENTES

**¿Qué es?** El archivo CSV con todos tus clientes.

**Qué necesita cada cliente:**

| Campo | Ejemplo | Obligatorio |
|-------|---------|-------------|
| **Nombre** | Juan López | ✅ Sí |
| **Email** | juan@empresa.com | ✅ Sí |
| **Empresa** | Tech Solutions SA | ✅ Sí |
| **Teléfono** | +56912345678 | ❌ Opcional |
| **Ciudad** | Santiago | ❌ Opcional |
| **Industria** | Tecnología | ❌ Opcional |
| **Monto** | 50000 | ❌ Opcional |
| **Estado** | Prospecto | ❌ Opcional |

**Formato:**
```
nombre,email,empresa,telefono,ciudad,industria,monto,estado
Juan López,juan@empresa.com,Tech Solutions,+56912345678,Santiago,Tecnología,50000,Prospecto
María García,maria@empresa.com,Marketing Pro,+56987654321,Valparaíso,Marketing,75000,Propuesta
Carlos Ruiz,carlos@empresa.com,E-commerce Inc,,Concepción,E-commerce,100000,Prospecto
```

**¿Dónde lo encuentras?**
- Excel/Google Sheets → Exportar como CSV
- CRM anterior → Descargar clientes
- Archivo existente → Ajustar formato

**Checklist:**
- [ ] Tengo la lista de clientes
- [ ] Tiene al menos nombre, email y empresa
- [ ] Los emails son válidos
- [ ] No hay duplicados

---

## 🛒 2. SHOPIFY (Si tienes tienda)

**¿Qué necesitas?**

1. **URL de tu tienda**
   - Ejemplo: `mitienda.myshopify.com`
   - Dónde encontrar: Dashboard → Settings

2. **API Key de Shopify**
   - Dónde encontrar: 
     1. Dashboard → Apps → App and sales channel settings
     2. Develop apps → Create an app
     3. Copiar "API Key"
   
3. **Access Token**
   - Dónde encontrar: Mismo lugar, "Admin API access token"

**Checklist:**
- [ ] Tengo URL de mi tienda
- [ ] Tengo API Key
- [ ] Tengo Access Token
- [ ] Shopify está activo y funcionando

---

## 📧 3. EMAIL (SendGrid)

**¿Qué necesitas?**

1. **Cuenta en SendGrid**
   - Ir a: https://sendgrid.com
   - Crear cuenta gratuita

2. **API Key**
   - Dónde encontrar:
     1. Dashboard → Settings → API Keys
     2. Create API Key → Copiar

3. **Email de envío**
   - Ejemplo: `noreply@enbuenamesa.com`
   - Debe estar verificado en SendGrid

**Checklist:**
- [ ] Tengo cuenta en SendGrid
- [ ] Tengo API Key
- [ ] Tengo email verificado
- [ ] Email de prueba funciona

---

## 💰 4. FACEBOOK ADS (Si usas Facebook Ads)

**¿Qué necesitas?**

1. **Token de Acceso**
   - Dónde encontrar: Facebook Graph API Explorer
   - O: Business Manager → Tools → Graph API Explorer

2. **ID de Cuenta de Negocio**
   - Dónde encontrar: Facebook Business Manager → Settings

**Checklist:**
- [ ] Tengo token de acceso
- [ ] Tengo ID de cuenta
- [ ] Token es válido (no expirado)

---

## 🔍 5. GOOGLE ADS (Si usas Google Ads)

**¿Qué necesitas?**

1. **Developer Token**
   - Dónde encontrar: Google Ads → Tools → API Center

2. **Client ID** (OAuth)
   - Dónde encontrar: Google Cloud Console → Credentials

3. **Client Secret**
   - Dónde encontrar: Mismo lugar

**Checklist:**
- [ ] Tengo Developer Token
- [ ] Tengo Client ID
- [ ] Tengo Client Secret

---

## 🔐 SEGURIDAD - GUARDAR SECRETOS

**IMPORTANTE:** Nunca compartas estas claves. Son como contraseñas.

**Dónde guardarlas:**
1. Archivo seguro en tu computadora (NO en email)
2. Gestor de contraseñas (1Password, LastPass)
3. O te las doy yo en el deployment

**Checklist:**
- [ ] Guardé todos los datos seguros
- [ ] No los compartí por email
- [ ] Nadie más conoce estos datos

---

## 📝 RESUMEN - LO MÍNIMO OBLIGATORIO

Para que el sistema funcione AHORA:

✅ **Obligatorio:**
- [ ] Lista de clientes (CSV con nombres, emails, empresas)
- [ ] Tu email de envío (puede ser test@gmail.com por ahora)

❌ **Opcional (agrega más tarde):**
- [ ] Shopify
- [ ] Facebook Ads
- [ ] Google Ads
- [ ] SendGrid (podemos usar test)

---

## 🚀 PRÓXIMO PASO

Cuando tengas listo:

1. Prepara archivo CSV de clientes
2. Avísame cuando esté listo
3. A las 16:00 hrs hacemos el deployment
4. El sistema carga los datos automáticamente

---

**¿Necesitas ayuda?** Solo avísame qué datos no tienes claro.
