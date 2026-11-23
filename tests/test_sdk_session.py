"""Exercise real Supabase SDK token propagation with HTTP transport simulated."""
import base64
import json
import time

import httpx
from supabase import ClientOptions, create_client


def test_sdk_keeps_sessions_separate_and_sends_user_token():
    seen=[]
    encode=lambda value: base64.urlsafe_b64encode(json.dumps(value).encode()).decode().rstrip('=')
    token=encode({'alg':'HS256','typ':'JWT'})+'.'+encode({'sub':'00000000-0000-0000-0000-000000000001','exp':int(time.time())+3600,'role':'authenticated'})+'.synthetic'
    user={'id':'00000000-0000-0000-0000-000000000001','aud':'authenticated','role':'authenticated','email':'test@example.invalid','email_confirmed_at':'2026-01-01T00:00:00Z','created_at':'2026-01-01T00:00:00Z','app_metadata':{},'user_metadata':{},'is_anonymous':False}
    def handler(request):
        seen.append((request.url.path,request.headers.get('authorization')))
        if request.url.path.endswith('/verify'):
            return httpx.Response(200,json={'access_token':token,'refresh_token':'synthetic-refresh','token_type':'bearer','expires_in':3600,'user':user})
        if request.url.path.endswith('/user'): return httpx.Response(200,json=user)
        if request.url.path.endswith('/logout'): return httpx.Response(204)
        return httpx.Response(200,json=[])
    def new_client():
        return create_client('https://example.supabase.co','sb_publishable_synthetic', options=ClientOptions(httpx_client=httpx.Client(transport=httpx.MockTransport(handler)), auto_refresh_token=False))
    a,b=new_client(),new_client()
    a.auth.verify_otp({'email':'test@example.invalid','token':'synthetic','type':'email'})
    assert a.auth.get_user().user.email_confirmed_at
    assert b.auth.get_session() is None
    a.table('participants').select('*').execute()
    assert seen[-1][1]=='Bearer '+token
    b.table('participants').select('*').execute()
    assert seen[-1][1]=='Bearer sb_publishable_synthetic'
    a.auth.sign_out()
    assert a.auth.get_session() is None
    a.table('participants').select('*').execute()
    assert seen[-1][1]=='Bearer sb_publishable_synthetic'
