# nvt-copilot-studio-facebook-workplace
nvt-copilot-studio-facebook-workplace

## Flow
1. Get the direct line token
	- Get directline URL from `Channels` tab  > `Mobile app` > `Token Endpoint` inside **copilot studio**, it should look like this: `https://<randomid>.0d.environment.api.powerplatform.com/powervirtualagents/botsbyschema/cr69a_copilot1/directline/token?api-version=2022-03-01-preview`
	- Make a `GET` API request to the endpoint to get the token, this token we will use to create a conversation. ![[Pasted image 20240310201524.png]]
	- ref: [Direct Line Authentication in Azure AI Bot Service - Bot Service | Microsoft Learn](https://learn.microsoft.com/en-us/azure/bot-service/rest-api/bot-framework-rest-direct-line-3-0-authentication?view=azure-bot-service-4.0)
2. Start a conversation:
	- Using the directline token from **step 1** as **Bearer token**, make a `POST` API request to `https://directline.botframework.com/v3/directline/conversations/` to create a conversation.
	- Store these informations *(because we will be using them later)*:
		- `conversationId`: the conversation id ![[Pasted image 20240310195143.png]]
		- `token`: the conversation token ![[Pasted image 20240310195255.png]]
	- **Notes**:
		- the `token` has expire time, can check that in `expires_in` field, default is 3600 seconds.
		- If using **websocket** then you can use the `streamUrl` for websocket connection ![[Pasted image 20240310195535.png]]
	- ref: [Start a conversation - Bot Service | Microsoft Learn](https://learn.microsoft.com/en-us/azure/bot-service/rest-api/bot-framework-rest-direct-line-3-0-start-conversation?view=azure-bot-service-4.0)
1. Post activity *(or send messages)*:
	- 
	- ref: [Send an activity the bot - Bot Service | Microsoft Learn](https://learn.microsoft.com/en-us/azure/bot-service/rest-api/bot-framework-rest-direct-line-3-0-send-activity?view=azure-bot-service-4.0)
3. Get activities *(or receive messages)*:

reference: [Add a chatbot to mobile and web apps - Microsoft Copilot Studio | Microsoft Learn](https://learn.microsoft.com/en-us/microsoft-copilot-studio/publication-connect-bot-to-custom-application)

Facebook messenger does not have websocket protocol, that's why we are using Copilot Studio Directline API instead of websocket.
