# Bot Gen :

main.py comport le code du bot

# Variables :

**Les variables doivent être absolument changé !**

color = color en html ou hexa du bot !
admin_role_id = id du role pour pouvoir ajouter des services ,des comptes ect....
vip_role_id = id du role vip
booster_role_id = id du role booster
server_id = id du server principal
cooldown = cooldown entre chaque generation
gen_free_channel_id = id du salon free
gen_vip_channel_id = id du salon vip
gen_booster_channel_id = id du salon booster

# Database Connection :

**Changer avec vos infos :**

def create_connection():
    try:
        connection = mysql.connector.connect(
            host="ip ou localhost",
            user="username",
            password="mdp",
            database="nom de la database"
        )
        if connection.is_connected():
            print("Connection to database was successful")
            return connection
    except Error as e:
        print(f"Error: '{e}'")
        return None

# Token bot :

**la ligne a la fin !**

bot.run('TOKEN_DU_BOT')


**Et il suffit de l'herger ensuite sur votre hebergeur ou un hebergeur free (nethost.fr ,daki.cc)**
