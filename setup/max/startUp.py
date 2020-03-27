try:
    from avalon import api, max_
    api.install(max_)
except Exception as e:
    print("startUp: " + str(e))
