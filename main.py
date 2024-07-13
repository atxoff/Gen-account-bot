import discord
from discord.ext import commands
from discord import app_commands
import mysql.connector
from mysql.connector import Error
import asyncio

# Configurer les intents
intents = discord.Intents.all()

# Créer une instance de bot
bot = commands.Bot(command_prefix='+', intents=intents)

color = color en html ou hexa du bot !
admin_role_id = id du role pour pouvoir ajouter des services ,des comptes ect....
vip_role_id = id du role vip
booster_role_id = id du role booster
server_id = id du server principal
cooldown = cooldown entre chaque generation
gen_free_channel_id = id du salon free
gen_vip_channel_id = id du salon vip
gen_booster_channel_id = id du salon booster

# Dictionnaire pour gérer le cooldown par utilisateur
user_cooldowns = {}

# Définir le statut personnalisé en streaming
@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    await bot.change_presence(activity=discord.Streaming(name="Galaxy", url="https://www.twitch.tv/galaxy"))

@bot.tree.command(name="help", description="Affiche la liste des commandes disponibles pour tous les utilisateurs")
async def help_command(interaction: discord.Interaction):
    embed_color = hex_to_discord_color(color)
    embed = discord.Embed(title="Commandes disponibles", description="Voici les commandes que vous pouvez utiliser :", color=embed_color)

    commands = [
        {"name": "genfree", "description": "Génère un compte gratuit.", "usage": "/genfree <service>"},
        {"name": "genvip", "description": "Génère un compte VIP.", "usage": "/genvip <service>"},
        {"name": "genbooster", "description": "Génère un compte Booster.", "usage": "/genbooster <service>"},
        {"name": "stock", "description": "Affiche le stock de comptes disponibles pour le rôle spécifié.", "usage": "/stock <role>"},
        {"name": "ping", "description": "Vérifie la latence du bot.", "usage": "/ping"},
        {"name": "help", "description": "Affiche la liste des commandes disponibles.", "usage": "/help"}
    ]

    for command in commands:
        embed.add_field(name=f"**/{command['name']}**", value=f"*{command['description']}*\n`{command['usage']}`", inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="helpstaff", description="Affiche la liste des commandes disponibles pour le staff")
async def help_staff_command(interaction: discord.Interaction):
    guild = interaction.guild
    admin_role = guild.get_role(admin_role_id)

    # Vérifier si l'utilisateur a le rôle administrateur
    if admin_role and admin_role in interaction.user.roles:
        embed_color = hex_to_discord_color(color)
        embed = discord.Embed(title="Commandes disponibles pour le staff", description="Voici les commandes réservées au staff :", color=embed_color)

        commands = [
            {"name": "addservice", "description": "Ajoute un service.", "usage": "/addservice"},
            {"name": "deleteservice", "description": "Supprime un service.", "usage": "/deleteservice"},
            {"name": "set", "description": "Définit une variable (color/admin_role/booster_role/vip_role/cooldown/gif).", "usage": "/set <color/admin_role/booster_role/vip_role/cooldown/gif> <value>"},
            {"name": "addvip", "description": "Ajoute le rôle VIP à l'utilisateur mentionné.", "usage": "/addvip <user>"},
            {"name": "addbooster", "description": "Ajoute le rôle Booster à l'utilisateur mentionné.", "usage": "/addbooster <user>"},
            {"name": "addadminperm", "description": "Ajoute le rôle administrateur à l'utilisateur mentionné.", "usage": "/addadminperm <user>"},
            {"name": "addstockfile", "description": "Ajoute des comptes depuis un fichier dans le service spécifiée.", "usage": "/addstockfile <service> <role>"},
            {"name": "addstockmsg", "description": "Ajoute des comptes depuis un message dans le service spécifiée.", "usage": "/addstockmsg <service> <role>"},
            {"name": "resetstock", "description": "Vide un stock d'un service.", "usage": "/resetstock <service>"},
            {"name": "resetallstock", "description": "Vide tous le stock de tous les services.", "usage": "/resetallstock"}
        ]

        for command in commands:
            embed.add_field(name=f"**/{command['name']}**", value=f"*{command['description']}*\n`{command['usage']}`", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(title="Permission refusée", description="Vous n'avez pas la permission d'exécuter cette commande.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)


# Commande pour afficher la latence du bot
@bot.tree.command(name="ping", description="Affiche la latence du bot")
async def ping(interaction: discord.Interaction):
    latency = bot.latency * 1000  # Convertir en millisecondes
    embed_color = hex_to_discord_color(color)
    embed = discord.Embed(title="🏓 Pong!", description=f"La latence du bot est de `{latency:.2f}`ms !", color=embed_color)
    await interaction.response.send_message(embed=embed)

# Fonction pour convertir un code couleur hexadécimal en discord.Color
def hex_to_discord_color(hex_color):
    return discord.Color(int(hex_color.strip("#"), 16))

# Vérificateur de permissions pour les commandes administratives
def is_admin():
    async def predicate(interaction: discord.Interaction):
        return interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)

# Fonction pour récupérer un objet discord.Role à partir de l'ID ou de la mention de rôle
async def get_role(guild: discord.Guild, role_id: str):
    role_id = role_id.strip("<>@&!")  # Retirer les caractères inutiles de la mention de rôle
    try:
        role = guild.get_role(int(role_id))
    except ValueError:
        role = discord.utils.get(guild.roles, name=role_id)
    return role

@bot.tree.command(name="genfree", description="Génère un compte")
async def generate_free_account(interaction: discord.Interaction, service: str):
    global cooldown, gen_free_channel_id

    # Vérifier si la commande est exécutée dans le bon salon
    if interaction.channel_id != gen_free_channel_id:
        embed = discord.Embed(title="Commande restreinte", description=f"Cette commande ne peut être exécutée que dans <#{gen_free_channel_id}>.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Récupérer l'utilisateur ayant exécuté la commande
    user_id = interaction.user.id

    # Vérifier le cooldown par utilisateur
    if user_id in user_cooldowns and user_cooldowns[user_id] > 0:
        remaining_cooldown = user_cooldowns[user_id]
        embed = discord.Embed(title="Cooldown actif", description=f"Merci d'attendre encore {remaining_cooldown} secondes avant de pouvoir exécuter à nouveau cette commande.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Vérifier s'il y a un compte free disponible dans la table
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(f"SELECT Compte FROM {service} WHERE Role='free' LIMIT 1")
            row = cursor.fetchone()  # Récupérer la première ligne

            if row:
                account = row[0]
                email, password = account.split(':')

                # Supprimer la ligne de compte de la table
                cursor.execute(f"DELETE FROM {service} WHERE Compte='{account}'")
                connection.commit()

                # Envoyer le compte en MP à l'utilisateur
                user = interaction.user
                try:
                    await user.send(f"**Voici votre compte `{service}` :**\n\n"
                                    f"**E-mail :**\n```{email}```\n\n"
                                    f"**Mot de passe :**\n```{password}```")
                    embed_color = hex_to_discord_color(color)
                    embed = discord.Embed(title="Génération exécutée", description=f"Votre compte `{service}` vous a été envoyé en MP.", color=embed_color)
                    embed.set_image(url="https://share.creavite.co/66912bc3f5670e0948f8d8e7.gif")
                    await interaction.response.send_message(embed=embed, ephemeral=False)

                    # Activer le cooldown par utilisateur
                    user_cooldowns[user_id] = cooldown  # Assigner le cooldown général par utilisateur
                    await asyncio.sleep(cooldown)
                    user_cooldowns[user_id] = 0  # Réinitialiser le cooldown après expiration
                except discord.Forbidden:
                    embed = discord.Embed(title="Erreur", description="Impossible de vous envoyer le compte en MP. Veuillez autoriser les messages privés.", color=discord.Color.red())
                    await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(title="Aucun compte disponible", description=f"Aucun compte free disponible pour `{service}`.", color=discord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(title="Erreur", description=f"Erreur lors de la génération du compte : {e}", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        finally:
            cursor.close()
            connection.close()
    else:
        embed = discord.Embed(title="Erreur de connexion", description="Erreur de connexion à la base de données", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="genvip", description="Génère un compte")
async def generate_vip_account(interaction: discord.Interaction, service: str):
    global cooldown, gen_vip_channel_id

    # Vérifier si la commande est exécutée dans le bon salon
    if interaction.channel_id != gen_vip_channel_id:
        embed = discord.Embed(title="Commande restreinte", description=f"Cette commande ne peut être exécutée que dans <#{gen_vip_channel_id}>.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Récupérer l'utilisateur ayant exécuté la commande
    user_id = interaction.user.id

    # Vérifier le cooldown par utilisateur
    if user_id in user_cooldowns and user_cooldowns[user_id] > 0:
        remaining_cooldown = user_cooldowns[user_id]
        embed = discord.Embed(title="Cooldown actif", description=f"Merci d'attendre encore {remaining_cooldown} secondes avant de pouvoir exécuter à nouveau cette commande.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Vérifier s'il y a un compte VIP disponible dans la table
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(f"SELECT Compte FROM {service} WHERE Role='vip' LIMIT 1")
            row = cursor.fetchone()  # Récupérer la première ligne

            if row:
                account = row[0]
                email, password = account.split(':')

                # Supprimer la ligne de compte de la table
                cursor.execute(f"DELETE FROM {service} WHERE Compte='{account}'")
                connection.commit()

                # Envoyer le compte en MP à l'utilisateur
                user = interaction.user
                try:
                    await user.send(f"**Voici votre compte `{service}` (VIP) :**\n\n"
                                    f"**E-mail :**\n```{email}```\n\n"
                                    f"**Mot de passe :**\n```{password}```")
                    embed_color = hex_to_discord_color(color)
                    embed = discord.Embed(title="Génération exécutée", description=f"Votre compte `{service}` (VIP) vous a été envoyé en MP.", color=embed_color)
                    embed.set_image(url="https://share.creavite.co/66912bc3f5670e0948f8d8e7.gif")
                    await interaction.response.send_message(embed=embed, ephemeral=False)

                    # Activer le cooldown par utilisateur
                    user_cooldowns[user_id] = cooldown  # Assigner le cooldown général par utilisateur
                    await asyncio.sleep(cooldown)
                    user_cooldowns[user_id] = 0  # Réinitialiser le cooldown après expiration
                except discord.Forbidden:
                    embed = discord.Embed(title="Erreur", description="Impossible de vous envoyer le compte en MP. Veuillez autoriser les messages privés.", color=discord.Color.red())
                    await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(title="Aucun compte disponible", description=f"Aucun compte VIP disponible pour `{service}`.", color=discord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(title="Erreur", description=f"Erreur lors de la génération du compte : {e}", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        finally:
            cursor.close()
            connection.close()
    else:
        embed = discord.Embed(title="Erreur de connexion", description="Erreur de connexion à la base de données", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="genbooster", description="Génère un compte Booster à partir de la table spécifiée")
async def generate_booster_account(interaction: discord.Interaction, service: str):
    global cooldown, gen_booster_channel_id

    # Vérifier si la commande est exécutée dans le bon salon
    if interaction.channel_id != gen_booster_channel_id:
        embed = discord.Embed(title="Commande restreinte", description=f"Cette commande ne peut être exécutée que dans <#{gen_booster_channel_id}>.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Récupérer l'utilisateur ayant exécuté la commande
    user_id = interaction.user.id

    # Vérifier le cooldown par utilisateur
    if user_id in user_cooldowns and user_cooldowns[user_id] > 0:
        remaining_cooldown = user_cooldowns[user_id]
        embed = discord.Embed(title="Cooldown actif", description=f"Merci d'attendre encore {remaining_cooldown} secondes avant de pouvoir exécuter à nouveau cette commande.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Vérifier s'il y a un compte Booster disponible dans la table
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute(f"SELECT Compte FROM {service} WHERE Role='booster' LIMIT 1")
            row = cursor.fetchone()  # Récupérer la première ligne

            if row:
                account = row[0]
                email, password = account.split(':')

                # Supprimer la ligne de compte de la table
                cursor.execute(f"DELETE FROM {service} WHERE Compte='{account}'")
                connection.commit()

                # Envoyer le compte en MP à l'utilisateur
                user = interaction.user
                try:
                    await user.send(f"**Voici votre compte `{service}` (Booster) :**\n\n"
                                    f"**E-mail :**\n```{email}```\n\n"
                                    f"**Mot de passe :**\n```{password}```")
                    embed_color = hex_to_discord_color(color)
                    embed = discord.Embed(title="Génération exécutée", description=f"Votre compte `{service}` (Booster) vous a été envoyé en MP.", color=embed_color)
                    embed.set_image(url="https://share.creavite.co/66912bc3f5670e0948f8d8e7.gif")
                    await interaction.response.send_message(embed=embed, ephemeral=False)

                    # Activer le cooldown par utilisateur
                    user_cooldowns[user_id] = cooldown  # Assigner le cooldown général par utilisateur
                    await asyncio.sleep(cooldown)
                    user_cooldowns[user_id] = 0  # Réinitialiser le cooldown après expiration
                except discord.Forbidden:
                    embed = discord.Embed(title="Erreur", description="Impossible de vous envoyer le compte en MP. Veuillez autoriser les messages privés.", color=discord.Color.red())
                    await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(title="Aucun compte disponible", description=f"Aucun compte Booster disponible pour `{service}`.", color=discord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(title="Erreur", description=f"Erreur lors de la génération du compte : {e}", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        finally:
            cursor.close()
            connection.close()
    else:
        embed = discord.Embed(title="Erreur de connexion", description="Erreur de connexion à la base de données", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="setcooldown", description="Définit le cooldown pour le bot")
async def set_cooldown(interaction: discord.Interaction, seconds: int):
    guild = interaction.guild
    admin_role = guild.get_role(admin_role_id)
    if admin_role and admin_role in interaction.user.roles:
        update_code_variable("cooldown", seconds)
        embed_color = hex_to_discord_color(color)
        embed = discord.Embed(title="Cooldown mis à jour", description=f"Le cooldown a été défini sur `{seconds}` secondes.", color=embed_color)
        await interaction.response.send_message(embed=embed, ephemeral=True)  # ephemeral=True pour que seule la personne qui a exécuté la commande puisse voir
    else:
        embed = discord.Embed(title="Permission refusée", description="Vous n'avez pas la permission d'exécuter cette commande.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)  # ephemeral=True pour que seule la personne qui a exécuté la commande puisse voir

@bot.tree.command(name="setchannelfree", description="Définit le salon de génération pour les utilisateurs free")
async def set_channel_free(interaction: discord.Interaction, channel: discord.TextChannel):
    guild = interaction.guild
    admin_role = guild.get_role(admin_role_id)
    if admin_role and admin_role in interaction.user.roles:
        global gen_free_channel_id
        gen_free_channel_id = channel.id
        embed_color = hex_to_discord_color(color)
        embed = discord.Embed(title="Salon de génération pour les utilisateurs free défini", description=f"Le salon de génération pour les utilisateurs free a été défini sur {channel.mention}", color=embed_color)
        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Mettre à jour le code du bot avec le nouvel ID de salon
        update_code_variable("gen_free_channel_id", str(channel.id))
    else:
        embed = discord.Embed(title="Permission refusée", description="Vous n'avez pas la permission d'exécuter cette commande.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="setchannelvip", description="Définit le salon de génération pour les utilisateurs VIP")
async def set_channel_vip(interaction: discord.Interaction, channel: discord.TextChannel):
    guild = interaction.guild
    admin_role = guild.get_role(admin_role_id)
    if admin_role and admin_role in interaction.user.roles:
        global gen_vip_channel_id
        gen_vip_channel_id = channel.id
        embed_color = hex_to_discord_color(color)
        embed = discord.Embed(title="Salon de génération pour les utilisateurs VIP défini", description=f"Le salon de génération pour les utilisateurs VIP a été défini sur {channel.mention}", color=embed_color)
        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Mettre à jour le code du bot avec le nouvel ID de salon VIP
        update_code_variable("gen_vip_channel_id", str(channel.id))
    else:
        embed = discord.Embed(title="Permission refusée", description="Vous n'avez pas la permission d'exécuter cette commande.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="setchannelbooster", description="Définit le salon de génération pour les utilisateurs Booster")
async def set_channel_booster(interaction: discord.Interaction, channel: discord.TextChannel):
    guild = interaction.guild
    admin_role = guild.get_role(admin_role_id)
    if admin_role and admin_role in interaction.user.roles:
        global gen_booster_channel_id
        gen_booster_channel_id = channel.id
        embed_color = hex_to_discord_color(color)
        embed = discord.Embed(title="Salon de génération pour les utilisateurs Booster défini", description=f"Le salon de génération pour les utilisateurs Booster a été défini sur {channel.mention}", color=embed_color)
        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Mettre à jour le code du bot avec le nouvel ID de salon Booster
        update_code_variable("gen_booster_channel_id", str(channel.id))
    else:
        embed = discord.Embed(title="Permission refusée", description="Vous n'avez pas la permission d'exécuter cette commande.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="addstockfile", description="Ajout du stock a un service via un fichier .txt")
async def add_stock_file(interaction: discord.Interaction, service: str, role: str):
    guild = interaction.guild
    admin_role = guild.get_role(admin_role_id)
    
    if admin_role and admin_role in interaction.user.roles:
        embed_color = hex_to_discord_color(color)
        embed = discord.Embed(title="Envoyez le fichier", description=f"Veuillez envoyer le fichier `.txt` pour le service `{service}`.", color=embed_color)
        await interaction.response.send_message(embed=embed)

        def check_file(msg):
            return msg.author == interaction.user and msg.attachments and msg.attachments[0].filename.endswith('.txt')

        try:
            msg = await bot.wait_for('message', check=check_file, timeout=120)
            file = msg.attachments[0]
            content = (await file.read()).decode('utf-8').splitlines()

            connection = create_connection()
            if connection:
                try:
                    cursor = connection.cursor()
                    for line in content:
                        cursor.execute(f"INSERT INTO {service} (Compte, Role) VALUES (%s, %s)", (line, role))
                    connection.commit()
                    embed = discord.Embed(title="Fichier ajouté avec succès", description=f"Le fichier a été ajouté à `{service}` avec le rôle `{role}`.", color=embed_color)
                    await interaction.followup.send(embed=embed, ephemeral=False)
                except Error as e:
                    embed = discord.Embed(title="Erreur", description=f"Erreur lors de l'ajout des données: {e}", color=discord.Color.red())
                    await interaction.followup.send(embed=embed, ephemeral=True)
                finally:
                    cursor.close()
                    connection.close()
            await msg.delete()
        except TimeoutError:
            embed = discord.Embed(title="Temps écoulé", description="Vous n'avez pas envoyé de fichier à temps.", color=discord.Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(title="Permission refusée", description="Vous n'avez pas la permission d'exécuter cette commande.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)



@bot.tree.command(name="addstockmsg", description="Ajout de stock a un service via un message")
async def add_stock_msg(interaction: discord.Interaction, service: str, role: str):
    guild = interaction.guild
    admin_role = guild.get_role(admin_role_id)
    
    if admin_role and admin_role in interaction.user.roles:
        embed_color = hex_to_discord_color(color)
        embed = discord.Embed(title="Envoyez le message", description=f"Veuillez envoyer le message pour le service `{service}`.", color=embed_color)
        await interaction.response.send_message(embed=embed)

        def check_msg(msg):
            return msg.author == interaction.user and msg.content

        try:
            msg = await bot.wait_for('message', check=check_msg, timeout=120)
            content = msg.content.splitlines()

            connection = create_connection()
            if connection:
                try:
                    cursor = connection.cursor()
                    for line in content:
                        cursor.execute(f"INSERT INTO {service} (Compte, Role) VALUES (%s, %s)", (line, role))
                    connection.commit()
                    embed = discord.Embed(title="Message ajouté avec succès", description=f"Le message a été ajouté à `{service}` avec le rôle `{role}`.", color=embed_color)
                    await interaction.followup.send(embed=embed, ephemeral=False)
                except Error as e:
                    embed = discord.Embed(title="Erreur", description=f"Erreur lors de l'ajout des données: {e}", color=discord.Color.red())
                    await interaction.followup.send(embed=embed, ephemeral=True)
                finally:
                    cursor.close()
                    connection.close()
            await msg.delete()
        except TimeoutError:
            embed = discord.Embed(title="Temps écoulé", description="Vous n'avez pas envoyé de message à temps.", color=discord.Color.red())
            await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(title="Permission refusée", description="Vous n'avez pas la permission d'exécuter cette commande.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="addvip", description="Ajoute le rôle VIP à l'utilisateur mentionné")
async def add_vip(interaction: discord.Interaction, member: discord.Member):
    guild = interaction.guild
    admin_role = guild.get_role(admin_role_id)
    vip_role = guild.get_role(vip_role_id)
    if admin_role and admin_role in interaction.user.roles:
        if vip_role:
            await member.add_roles(vip_role)
            embed_color = hex_to_discord_color(color)
            embed = discord.Embed(title="Rôle VIP ajouté", description=f"{member.mention} a reçu le rôle VIP.", color=embed_color)
            await interaction.response.send_message(embed=embed, ephemeral=False)
        else:
            embed = discord.Embed(title="Erreur", description="Le rôle VIP n'existe pas.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(title="Permission refusée", description="Vous n'avez pas la permission d'exécuter cette commande.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="addbooster", description="Ajoute le rôle Booster à l'utilisateur mentionné")
async def add_booster(interaction: discord.Interaction, member: discord.Member):
    guild = interaction.guild
    admin_role = guild.get_role(admin_role_id)
    booster_role = guild.get_role(booster_role_id)
    if admin_role and admin_role in interaction.user.roles:
        if booster_role:
            await member.add_roles(booster_role)
            embed_color = hex_to_discord_color(color)
            embed = discord.Embed(title="Rôle Booster ajouté", description=f"{member.mention} a reçu le rôle Booster.", color=embed_color)
            await interaction.response.send_message(embed=embed, ephemeral=False)
        else:
            embed = discord.Embed(title="Erreur", description="Le rôle Booster n'existe pas.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(title="Permission refusée", description="Vous n'avez pas la permission d'exécuter cette commande.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="addadminrole", description="Ajoute le rôle Administrateur à l'utilisateur mentionné")
async def add_adminrole(interaction: discord.Interaction, member: discord.Member):
    guild = interaction.guild
    admin_role = guild.get_role(admin_role_id)
    if admin_role and admin_role in interaction.user.roles:
        if admin_role:
            await member.add_roles(admin_role)
            embed_color = hex_to_discord_color(color)
            embed = discord.Embed(title="Rôle Administrateur ajouté", description=f"{member.mention} a reçu le rôle Administrateur.", color=embed_color)
            await interaction.response.send_message(embed=embed, ephemeral=False)
        else:
            embed = discord.Embed(title="Erreur", description="Le rôle Administrateur n'existe pas.", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(title="Permission refusée", description="Vous n'avez pas la permission d'exécuter cette commande.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)


# Commande pour définir la couleur d'embed
@bot.tree.command(name="setcolor", description="Définit la couleur d'embed du bot")
@is_admin()
async def set_color(interaction: discord.Interaction, hex_color: str):
    global color
    color = hex_color  # Mettre à jour la variable globale
    embed_color = hex_to_discord_color(color)
    embed = discord.Embed(title="Couleur d'embed mise à jour", description=f"La couleur d'embed a été définie sur `{hex_color}`.", color=embed_color)
    await interaction.response.send_message(embed=embed, ephemeral=True)  # ephemeral=True pour que seul l'utilisateur voit la réponse

    # Mettre à jour le code du bot avec la nouvelle couleur
    update_code_variable("color", hex_color)

# Commande pour définir l'ID du rôle administrateur
@bot.tree.command(name="setadminrole", description="Définit l'ID du rôle administrateur")
@is_admin()
async def set_admin_role(interaction: discord.Interaction, role_id: str):
    global admin_role_id
    guild = interaction.guild
    role = await get_role(guild, role_id)
    if role:
        admin_role_id = role.id  # Mettre à jour la variable globale avec l'ID du rôle
        embed_color = hex_to_discord_color(color)
        embed = discord.Embed(title="ID du rôle administrateur mis à jour", description=f"L'ID du rôle administrateur a été défini sur `{role.name}` (`{role.id}`).", color=embed_color)
        await interaction.response.send_message(embed=embed, ephemeral=True)  # ephemeral=True pour que seul l'utilisateur voit la réponse

        # Mettre à jour le code du bot avec le nouvel ID de rôle administrateur
        update_code_variable("admin_role_id", str(role.id))
    else:
        embed = discord.Embed(title="Erreur", description=f"Impossible de trouver le rôle `{role_id}`.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)  # ephemeral=True pour que seul l'utilisateur voit la réponse

# Commande pour définir l'ID du rôle VIP
@bot.tree.command(name="setviprole", description="Définit l'ID du rôle VIP")
@is_admin()
async def set_vip_role(interaction: discord.Interaction, role_id: str):
    global vip_role_id
    guild = interaction.guild
    role = await get_role(guild, role_id)
    if role:
        vip_role_id = role.id  # Mettre à jour la variable globale avec l'ID du rôle
        embed_color = hex_to_discord_color(color)
        embed = discord.Embed(title="ID du rôle VIP mis à jour", description=f"L'ID du rôle VIP a été défini sur `{role.name}` (`{role.id}`).", color=embed_color)
        await interaction.response.send_message(embed=embed, ephemeral=True)  # ephemeral=True pour que seul l'utilisateur voit la réponse

        # Mettre à jour le code du bot avec le nouvel ID de rôle VIP
        update_code_variable("vip_role_id", str(role.id))
    else:
        embed = discord.Embed(title="Erreur", description=f"Impossible de trouver le rôle `{role_id}`.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)  # ephemeral=True pour que seul l'utilisateur voit la réponse

# Commande pour définir l'ID du rôle Booster
@bot.tree.command(name="setboosterrole", description="Définit l'ID du rôle Booster")
@is_admin()
async def set_booster_role(interaction: discord.Interaction, role_id: str):
    global booster_role_id
    guild = interaction.guild
    role = await get_role(guild, role_id)
    if role:
        booster_role_id = role.id  # Mettre à jour la variable globale avec l'ID du rôle
        embed_color = hex_to_discord_color(color)
        embed = discord.Embed(title="ID du rôle Booster mis à jour", description=f"L'ID du rôle Booster a été défini sur `{role.name}` (`{role.id}`).", color=embed_color)
        await interaction.response.send_message(embed=embed, ephemeral=True)  # ephemeral=True pour que seul l'utilisateur voit la réponse

        # Mettre à jour le code du bot avec le nouvel ID de rôle Booster
        update_code_variable("booster_role_id", str(role.id))
    else:
        embed = discord.Embed(title="Erreur", description=f"Impossible de trouver le rôle `{role_id}`.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)  # ephemeral=True pour que seul l'utilisateur voit la réponse

# Fonction pour mettre à jour la variable dans le code du bot
def update_code_variable(variable_name, new_value):
    with open("app.py", "r") as file:
        lines = file.readlines()
    with open("app.py", "w") as file:
        for line in lines:
            if line.startswith(f"{variable_name} = "):
                line = f"{variable_name} = {new_value}\n"
            file.write(line)

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

# Commande pour ajouter un service (table)
@bot.tree.command(name="addservice", description="Crée un nouveau service")
async def add_service(interaction: discord.Interaction, service: str):
    # Vérifier que l'utilisateur a le rôle d'administrateur pour accéder à cette commande
    guild = interaction.guild
    admin_role = guild.get_role(admin_role_id)
    if admin_role and admin_role in interaction.user.roles:
        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {service} (
                        Compte VARCHAR(255) NOT NULL,
                        Role VARCHAR(255) NOT NULL
                    )
                """)
                connection.commit()
                embed_color = hex_to_discord_color(color)
                embed = discord.Embed(title="Service ajouté avec succès", description=f"La service `{service}` a été créée avec succès !", color=embed_color)
                await interaction.response.send_message(embed=embed, ephemeral=False)  # ephemeral=False pour que tout le monde puisse voir
            except Error as e:
                embed = discord.Embed(title="Erreur lors de l'ajout du service", description=f"Erreur lors de la création de la table `{service}`: {e}", color=discord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=False)  # ephemeral=False pour que tout le monde puisse voir
            finally:
                cursor.close()
                connection.close()
        else:
            embed = discord.Embed(title="Erreur de connexion", description="Erreur de connexion à la base de données", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=False)  # ephemeral=False pour que tout le monde puisse voir
    else:
        embed = discord.Embed(title="Permission refusée", description="Vous n'avez pas la permission d'exécuter cette commande.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=False)  # ephemeral=False pour que tout le monde puisse voir

# Commande pour supprimer un service (table)
@bot.tree.command(name="deleteservice", description="Supprime un service")
async def delete_service(interaction: discord.Interaction, service: str):
    # Vérifier que l'utilisateur a le rôle d'administrateur pour accéder à cette commande
    guild = interaction.guild
    admin_role = guild.get_role(admin_role_id)
    if admin_role and admin_role in interaction.user.roles:
        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute(f"DROP TABLE IF EXISTS {service}")
                connection.commit()
                embed_color = hex_to_discord_color(color)
                embed = discord.Embed(title="Service supprimé avec succès", description=f"Le service `{service}` a été supprimé avec succès !", color=embed_color)
                await interaction.response.send_message(embed=embed, ephemeral=False)  # ephemeral=False pour que tout le monde puisse voir
            except Error as e:
                embed = discord.Embed(title="Erreur lors de la suppression du service", description=f"Erreur lors de la suppression de la table `{service}`: {e}", color=discord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=False)  # ephemeral=False pour que tout le monde puisse voir
            finally:
                cursor.close()
                connection.close()
        else:
            embed = discord.Embed(title="Erreur de connexion", description="Erreur de connexion à la base de données", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=False)  # ephemeral=False pour que tout le monde puisse voir
    else:
        embed = discord.Embed(title="Permission refusée", description="Vous n'avez pas la permission d'exécuter cette commande.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=False)  # ephemeral=False pour que tout le monde puisse voir

@bot.tree.command(name="resetstock", description="Vide un service")
async def reset_stock(interaction: discord.Interaction, service: str):
    if admin_role_id in [role.id for role in interaction.user.roles]:
        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute(f"DELETE FROM {service}")
                connection.commit()
                embed_color = hex_to_discord_color(color)
                embed = discord.Embed(title="Service réinitialisé avec succès", description=f"Le service `{service}` a été vidée avec succès !", color=embed_color)
                await interaction.response.send_message(embed=embed, ephemeral=False)
            except Error as e:
                embed = discord.Embed(title="Erreur lors de la réinitialisation du service", description=f"Erreur lors de la vidange de la table `{service}`: {e}", color=discord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=False)
            finally:
                cursor.close()
                connection.close()
        else:
            embed = discord.Embed(title="Erreur de connexion", description="Erreur de connexion à la base de données", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=False)
    else:
        embed = discord.Embed(title="Permission refusée", description="Vous n'avez pas la permission d'exécuter cette commande.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=False)

@bot.tree.command(name="resetallstock", description="Vide tous le stock")
async def reset_all_stock(interaction: discord.Interaction):
    if admin_role_id in [role.id for role in interaction.user.roles]:
        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                for table in tables:
                    cursor.execute(f"DELETE FROM {table[0]}")
                connection.commit()
                embed_color = hex_to_discord_color(color)
                embed = discord.Embed(title="Tous les services réinitialisés avec succès", description="Toutes les services ont été vidées avec succès !", color=embed_color)
                await interaction.response.send_message(embed=embed, ephemeral=False)
            except Error as e:
                embed = discord.Embed(title="Erreur lors de la réinitialisation des services", description=f"Erreur lors de la vidange des tables: {e}", color=discord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=False)
            finally:
                cursor.close()
                connection.close()
        else:
            embed = discord.Embed(title="Erreur de connexion", description="Erreur de connexion à la base de données", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=False)
    else:
        embed = discord.Embed(title="Permission refusée", description="Vous n'avez pas la permission d'exécuter cette commande.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=False)

@bot.tree.command(name="stock", description="Affiche le stock de comptes en fonction du rôle choisi")
@app_commands.choices(role=[
    app_commands.Choice(name="free", value="free"),
    app_commands.Choice(name="vip", value="vip"),
    app_commands.Choice(name="booster", value="booster")
])
async def stock(interaction: discord.Interaction, role: app_commands.Choice[str]):
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            table_info = ""
            total_count = 0
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]} WHERE Role = %s", (role.value,))
                count = cursor.fetchone()[0]
                if count > 0:
                    table_info += f"**{table[0]}**\nNombre de comptes : {count}\n\n"
                    total_count += count
            
            if table_info == "":
                table_info = "Aucuns comptes."

            embed_color = hex_to_discord_color(color)
            embed = discord.Embed(title=f"📦 Stock de comptes pour le rôle '{role.name}'", description=table_info, color=embed_color)
            embed.set_footer(text=f"Total de comptes pour {role.name} : {total_count}")
            await interaction.response.send_message(embed=embed, ephemeral=False)
        except Error as e:
            embed = discord.Embed(title="Erreur lors de l'affichage du stock", description=f"Erreur lors de la récupération des données: {e}", color=discord.Color.red())
            await interaction.response.send_message(embed=embed, ephemeral=False)
        finally:
            cursor.close()
            connection.close()
    else:
        embed = discord.Embed(title="Erreur de connexion", description="Erreur de connexion à la base de données", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=False)


# Synchroniser les commandes slash
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'We have logged in as {bot.user} and synced commands.')
    await bot.change_presence(activity=discord.Streaming(name="Galaxy", url="https://www.twitch.tv/galaxy"))

# Démarrer le bot
bot.run('TOKEN_DU_BOT')
