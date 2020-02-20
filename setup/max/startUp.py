try:
    from avalon import api, max
    api.install(max)
except Exception as e:
    print("startUp: " + repr(e))
