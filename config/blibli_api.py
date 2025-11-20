"""
Blibli API Configuration
Update the headers and cookies here when they expire
"""

# API Headers
BLIBLI_HEADERS = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'id',
    'cache-control': 'no-cache',
    'channelid': 'web',
    'content-type': 'application/json;charset=UTF-8',
    'isjual': 'false',
    'params': '[object Object]',
    'priority': 'u=1, i',
    'sec-ch-ua': '"Chromium";v="142", "Brave";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-arch': '"arm"',
    'sec-ch-ua-bitness': '"64"',
    'sec-ch-ua-full-version-list': '"Chromium";v="142.0.0.0", "Brave";v="142.0.0.0", "Not_A Brand";v="99.0.0.0"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-model': '""',
    'sec-ch-ua-platform': '"macOS"',
    'sec-ch-ua-platform-version': '"15.5.0"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'sec-gpc': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
}


# API Cookies - UPDATE THESE WHEN THEY EXPIRE
BLIBLI_COOKIES = {
    'Blibli-User-Id': 'e554ebe6-ae81-487c-bc8b-04ce88f6ba8d',
    'Blibli-Is-Member': 'false',
    'Blibli-Is-Remember': 'false',
    'Blibli-Session-Id': '03d8b16c-88e8-4984-a626-4a6b1f68aeb1',
    'Blibli-Signature': 'c257e91c7602228370423d98b4cb38dac227ab6c',
    'Blibli-Device-Id': 'U.10f1f12e-8944-403d-ba87-72c8556f532b',
    'Blibli-Device-Id-Signature': 'bb2e8ea51e803d0f30cd5e29e6ef50609d3d715d',
    '_cfuvid': 'Z5OzX95YxLA6uw2rZzAJ3epdTPQWjAHvCPKw_n9J96Q-1763620261581-0.0.1.1-604800000',
    '__cf_bm': 'zAlt5aKVsPDOlhbBMFUo7O0QnZxMlFopjM2_c6IFWLc-1763630141-1.0.1.1-KfvVBjlRdxqPJgBxcDpJaGrpxGOd0e6Zr7l_feKiaFGztSr6iQzg6iH2VvnCccE.Kxu8V7eBybOxE4fqdKmVz2uBJ_.kgu5.jPjNxOkFjD0',
    'cf_clearance': '65YwwY3YrCVcjNauPBzQxjOd8kV7Ek4n360KKeaqOdE-1763630142-1.2.1.1-alDOEgx8CCE1YtP__rd6oq3r_cI4yc4e3GGG053En46m.CUTcSzoy1if8pu0_w5QUqv9gJq_TtkH83ntohzAKIqboi9c5JcD4haCcE9L.VNmVi9bXfl2PYoXduNOoMq36h6Yb_1GskcrMp4JgAG5tNoUz9k3GtKdIrl8BYv3PygFMG2jyj9mcpdIVhYflDCGY5VrBo2PHUVp8V74FoviyhaW2bkaB8Ci3_0TEDWJO2g',
    'Blibli-dv-token': 'JT__JASVuj3JH8xH6OpT0D_TwhL7QwNDor5A3GipQf1VI2',
    'g_state': '{"i_l":0,"i_ll":1763630423458,"i_b":"s2twB+WQjY18lYRd9k1WdXUaAoEfW1P0xrbN97MRf8Y"}',
    'forterToken': 'f325fa4658344ef58e3c361eb823a0df_1763630423316_164_UDAD43b-mnts-a9-r8_25ck_',
}

"""
HOW TO UPDATE COOKIES:

1. Open Chrome/Brave browser
2. Go to https://www.blibli.com
3. Open Developer Tools (F12)
4. Go to Network tab
5. Search for a product
6. Find the request to /backend/search/products
7. Right-click -> Copy -> Copy as cURL
8. Extract the cookies from the cURL command
9. Update BLIBLI_COOKIES dictionary above

Example from cURL:
--cookie 'Blibli-User-Id=xxx; Blibli-Session-Id=yyy; ...'

Becomes:
BLIBLI_COOKIES = {
    'Blibli-User-Id': 'xxx',
    'Blibli-Session-Id': 'yyy',
    ...
}
"""

