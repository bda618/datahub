from typing import Dict, List, Optional, Union

from datahub.emitter.mcp_patch_builder import MetadataPatchProposal
from datahub.metadata.schema_classes import (
    AccessLevelClass,
    ChangeAuditStampsClass,
    ChartInfoClass as ChartInfo,
    ChartTypeClass,
    EdgeClass as Edge,
    GlobalTagsClass as GlobalTags,
    GlossaryTermAssociationClass as Term,
    GlossaryTermsClass as GlossaryTerms,
    KafkaAuditHeaderClass,
    OwnerClass as Owner,
    OwnershipTypeClass,
    SystemMetadataClass,
    TagAssociationClass as Tag,
)
from datahub.specific.custom_properties import CustomPropertiesPatchHelper
from datahub.specific.ownership import OwnershipPatchHelper
from datahub.utilities.urns.tag_urn import TagUrn
from datahub.utilities.urns.urn import Urn


class ChartPatchBuilder(MetadataPatchProposal):
    def __init__(
        self,
        urn: str,
        system_metadata: Optional[SystemMetadataClass] = None,
        audit_header: Optional[KafkaAuditHeaderClass] = None,
    ) -> None:
        """
        Initializes a ChartPatchBuilder instance.

        Args:
            urn: The URN of the chart
            system_metadata: The system metadata of the chart (optional).
            audit_header: The Kafka audit header of the chart (optional).
        """
        super().__init__(
            urn, system_metadata=system_metadata, audit_header=audit_header
        )
        self.custom_properties_patch_helper = CustomPropertiesPatchHelper(
            self, ChartInfo.ASPECT_NAME
        )
        self.ownership_patch_helper = OwnershipPatchHelper(self)

    def add_owner(self, owner: Owner) -> "ChartPatchBuilder":
        """
        Adds an owner to the ChartPatchBuilder.

        Args:
            owner: The Owner object to add.

        Returns:
            The ChartPatchBuilder instance.
        """
        self.ownership_patch_helper.add_owner(owner)
        return self

    def remove_owner(
        self, owner: str, owner_type: Optional[OwnershipTypeClass] = None
    ) -> "ChartPatchBuilder":
        """
        Removes an owner from the ChartPatchBuilder.

        Args:
            owner: The owner to remove.
            owner_type: The ownership type of the owner (optional).

        Returns:
            The ChartPatchBuilder instance.

        Notes:
            `owner_type` is optional.
        """
        self.ownership_patch_helper.remove_owner(owner, owner_type)
        return self

    def set_owners(self, owners: List[Owner]) -> "ChartPatchBuilder":
        """
        Sets the owners of the ChartPatchBuilder.

        Args:
            owners: A list of Owner objects.

        Returns:
            The ChartPatchBuilder instance.
        """
        self.ownership_patch_helper.set_owners(owners)
        return self

    def add_input_edge(self, input: Union[Edge, Urn, str]) -> "ChartPatchBuilder":
        """
        Adds an input to the ChartPatchBuilder.

        Args:
            input: The input, which can be an Edge object, Urn object, or a string.

        Returns:
            The ChartPatchBuilder instance.

        Notes:
            If `input` is an Edge object, it is used directly. If `input` is a Urn object or string,
            it is converted to an Edge object and added with default audit stamps.
        """
        if isinstance(input, Edge):
            input_urn: str = input.destinationUrn
            input_edge: Edge = input
        elif isinstance(input, (Urn, str)):
            input_urn = str(input)

            input_edge = Edge(
                destinationUrn=input_urn,
                created=self._mint_auditstamp(),
                lastModified=self._mint_auditstamp(),
            )

        self._ensure_urn_type("dataset", [input_edge], "add_dataset")
        self._add_patch(
            ChartInfo.ASPECT_NAME,
            "add",
            path=f"/inputEdges/{self.quote(input_urn)}",
            value=input_urn,
        )
        return self

    def remove_input_edge(self, input: Union[str, Urn]) -> "ChartPatchBuilder":
        """
        Removes an input from the ChartPatchBuilder.

        Args:
            input: The input to remove, specified as a string or Urn object.

        Returns:
            The ChartPatchBuilder instance.
        """
        self._add_patch(
            ChartInfo.ASPECT_NAME,
            "remove",
            path=f"/inputEdges/{self.quote(str(input))}",
            value={},
        )
        return self

    def set_input_edges(self, inputs: List[Edge]) -> "ChartPatchBuilder":
        """
        Sets the input edges for the ChartPatchBuilder.

        Args:
            inputs: A list of Edge objects representing the input edges.

        Returns:
            The ChartPatchBuilder instance.

        Notes:
            This method replaces all existing inputs with the given inputs.
        """
        self._add_patch(
            ChartInfo.ASPECT_NAME,
            "add",
            path="/inputEdges",
            value=inputs,
        )
        return self

    def add_tag(self, tag: Tag) -> "ChartPatchBuilder":
        """
        Adds a tag to the ChartPatchBuilder.

        Args:
            tag: The Tag object representing the tag to be added.

        Returns:
            The ChartPatchBuilder instance.
        """
        self._add_patch(
            GlobalTags.ASPECT_NAME, "add", path=f"/tags/{tag.tag}", value=tag
        )
        return self

    def remove_tag(self, tag: Union[str, Urn]) -> "ChartPatchBuilder":
        """
        Removes a tag from the ChartPatchBuilder.

        Args:
            tag: The tag to remove, specified as a string or Urn object.

        Returns:
            The ChartPatchBuilder instance.
        """
        if isinstance(tag, str) and not tag.startswith("urn:li:tag:"):
            tag = TagUrn.create_from_id(tag)
        self._add_patch(GlobalTags.ASPECT_NAME, "remove", path=f"/tags/{tag}", value={})
        return self

    def add_term(self, term: Term) -> "ChartPatchBuilder":
        """
        Adds a glossary term to the ChartPatchBuilder.

        Args:
            term: The Term object representing the glossary term to be added.

        Returns:
            The ChartPatchBuilder instance.
        """
        self._add_patch(
            GlossaryTerms.ASPECT_NAME, "add", path=f"/terms/{term.urn}", value=term
        )
        return self

    def remove_term(self, term: Union[str, Urn]) -> "ChartPatchBuilder":
        """
        Removes a glossary term from the ChartPatchBuilder.

        Args:
            term: The term to remove, specified as a string or Urn object.

        Returns:
            The ChartPatchBuilder instance.
        """
        if isinstance(term, str) and not term.startswith("urn:li:glossaryTerm:"):
            term = "urn:li:glossaryTerm:" + term
        self._add_patch(
            GlossaryTerms.ASPECT_NAME, "remove", path=f"/terms/{term}", value={}
        )
        return self

    def set_custom_properties(
        self, custom_properties: Dict[str, str]
    ) -> "ChartPatchBuilder":
        """
        Sets the custom properties for the ChartPatchBuilder.

        Args:
            custom_properties: A dictionary containing the custom properties to be set.

        Returns:
            The ChartPatchBuilder instance.

        Notes:
            This method replaces all existing custom properties with the given dictionary.
        """
        self._add_patch(
            ChartInfo.ASPECT_NAME,
            "add",
            path="/customProperties",
            value=custom_properties,
        )
        return self

    def add_custom_property(self, key: str, value: str) -> "ChartPatchBuilder":
        """
        Adds a custom property to the ChartPatchBuilder.

        Args:
            key: The key of the custom property.
            value: The value of the custom property.

        Returns:
            The ChartPatchBuilder instance.
        """
        self.custom_properties_patch_helper.add_property(key, value)
        return self

    def remove_custom_property(self, key: str) -> "ChartPatchBuilder":
        """
        Removes a custom property from the ChartPatchBuilder.

        Args:
            key: The key of the custom property to remove.

        Returns:
            The ChartPatchBuilder instance.
        """
        self.custom_properties_patch_helper.remove_property(key)
        return self

    def set_title(self, title: str) -> "ChartPatchBuilder":
        assert title, "ChartInfo title should not be None"
        self._add_patch(
            ChartInfo.ASPECT_NAME,
            "add",
            path="/title",
            value=title,
        )

        return self

    def set_description(self, description: str) -> "ChartPatchBuilder":
        assert description, "DashboardInfo description should not be None"
        self._add_patch(
            ChartInfo.ASPECT_NAME,
            "add",
            path="/description",
            value=description,
        )

        return self

    def set_last_refreshed(self, last_refreshed: Optional[int]) -> "ChartPatchBuilder":
        if last_refreshed:
            self._add_patch(
                ChartInfo.ASPECT_NAME,
                "add",
                path="/lastRefreshed",
                value=last_refreshed,
            )

        return self

    def set_last_modified(
        self, last_modified: "ChangeAuditStampsClass"
    ) -> "ChartPatchBuilder":
        if last_modified:
            self._add_patch(
                ChartInfo.ASPECT_NAME,
                "add",
                path="/lastModified",
                value=last_modified,
            )

        return self

    def set_external_url(self, external_url: Optional[str]) -> "ChartPatchBuilder":
        if external_url:
            self._add_patch(
                ChartInfo.ASPECT_NAME,
                "add",
                path="/externalUrl",
                value=external_url,
            )
        return self

    def set_chart_url(self, dashboard_url: Optional[str]) -> "ChartPatchBuilder":
        if dashboard_url:
            self._add_patch(
                ChartInfo.ASPECT_NAME,
                "add",
                path="/chartUrl",
                value=dashboard_url,
            )

        return self

    def set_type(
        self, type: Union[None, Union[str, "ChartTypeClass"]] = None
    ) -> "ChartPatchBuilder":
        if type:
            self._add_patch(
                ChartInfo.ASPECT_NAME,
                "add",
                path="/type",
                value=type,
            )

        return self

    def set_access(
        self, access: Union[None, Union[str, "AccessLevelClass"]] = None
    ) -> "ChartPatchBuilder":
        if access:
            self._add_patch(
                ChartInfo.ASPECT_NAME,
                "add",
                path="/access",
                value=access,
            )

        return self

    def add_inputs(self, input_urns: Optional[List[str]]) -> "ChartPatchBuilder":
        if input_urns:
            for urn in input_urns:
                self._add_patch(
                    aspect_name=ChartInfo.ASPECT_NAME,
                    op="add",
                    path=f"/inputs/{urn}",
                    value=urn,
                )

        return self
