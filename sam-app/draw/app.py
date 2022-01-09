import json
import boto3
import random

# import requests

# functionality
# newhand
# seehand
# draw

def draw(hand,deck):
    handlist = hand.split(',')
    for card in handlist:
        deck.remove(card)
    val = hand + ',' + random.choice(deck)
    return val

def newhand(deck):
    return ",".join(random.sample(deck,2))

def evalhand(hand):
    aces = 0
    val = 0
    handlist = hand.split(',')
    for card in handlist:
        cardval = card.split('_')[1]
        if cardval == 'a':
            aces+=1
            val+=1
        elif cardval in ['j','q','k']:
            val+=10
        else:
            val+= int(cardval)
    while aces!=0 and val<12:
        val+=10
        aces-=1    
    return val    


def lambda_handler(event, context):

    username = str(event["requestContext"]["authorizer"]["claims"]["email"])
    client = boto3.client('dynamodb')
    
    deck = []
    suits = ["heart", "club", "spade", "diamond"]
    cards = ["a", "2", "3", "4", "5", "6", "7", "8", "9", "10", "j", "q", "k"]

    for suit in suits:
        for card in cards:
            deck.append("_".join([suit,card]))

    if event["queryStringParameters"] is not None and event["queryStringParameters"]["command"]=="unittest":
        totest = ["heart_k,heart_a", "heart_k,heart_a,heart_q", "heart_9,heart_a,club_a"]
        results = [evalhand(x) for x in totest]
        hand = json.dumps({
            'input': totest, 
            'output': results,
        })

    # if user wants a new hand
    elif event["queryStringParameters"] is not None and event["queryStringParameters"]["command"]=="newhand":
        hand = newhand(deck)

    # if user wants to see their hand or draw a new card then load the current deck from the db
    else:  
        response = client.get_item(
            TableName='backgammon-table',
            Key={
                'uid': {
                    "S": username
                }
            }
        )
        hand = response["Item"]["hand"]["S"]

        # if the user wanted to draw a card, draw them a card
        if (event["queryStringParameters"] is None or event["queryStringParameters"]["command"]!="gethand") and evalhand(hand)<21:
            hand = draw(hand, deck)
    
    # if the user made a change to their deck, update the database
    if event["queryStringParameters"] is None or event["queryStringParameters"]["command"]!="gethand":
        data = client.put_item(
            TableName='backgammon-table',
            Item={
                'uid': {
                    'S': username
                },
                'hand': {
                    'S': hand
                }
            }
        )

    handval =0
    if event["queryStringParameters"] is None or event["queryStringParameters"]["command"]!="unittest":
        handval = evalhand(hand)

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": hand,
                "value": handval
            }
        ),
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": True
        }
    }
