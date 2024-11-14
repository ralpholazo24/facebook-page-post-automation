interface InstagramPublishParams {
  imageUrl: string;
  caption: string;
  accessToken: string;
  instagramAccountId: string;
}

async function publishInstagramPost({ 
  imageUrl, 
  caption, 
  accessToken, 
  instagramAccountId 
}: InstagramPublishParams) {
  try {
    // Step 1: Create a container
    const createContainerResponse = await fetch(
      `https://graph.facebook.com/v21.0/${instagramAccountId}/media`,
      {
        method: 'POST',
        body: new URLSearchParams({
          image_url: imageUrl,
          caption: caption,
          access_token: accessToken,
        }),
      }
    );

    if (!createContainerResponse.ok) {
      const errorData = await createContainerResponse.json();
      throw new Error(`Container creation failed: ${JSON.stringify(errorData)}`);
    }

    const { id: creationId } = await createContainerResponse.json();

    // Step 2: Publish the container
    const publishResponse = await fetch(
      `https://graph.facebook.com/v21.0/${instagramAccountId}/media_publish`,
      {
        method: 'POST',
        body: new URLSearchParams({
          creation_id: creationId,
          access_token: accessToken,
        }),
      }
    );

    if (!publishResponse.ok) {
      const errorData = await publishResponse.json();
      throw new Error(`Publishing failed: ${JSON.stringify(errorData)}`);
    }

    return await publishResponse.json();
  } catch (error) {
    console.error('Error publishing to Instagram:', error);
    throw error;
  }
} 